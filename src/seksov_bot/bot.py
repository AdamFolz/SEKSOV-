from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from .domain import (
    DomainError,
    ensure_enough_remaining,
    parse_positive_decimal,
    validate_drug_unit,
    validate_route,
    validate_site,
)
from .keyboards import (
    BTN_CANCEL,
    BTN_HISTORY,
    BTN_LAST,
    BTN_NEW_BATCH,
    BTN_RECORD,
    BTN_STATUS,
    cancel_keyboard,
    main_keyboard,
    route_keyboard,
    site_keyboard,
)
from .messages import batch_status, injection_line, saved_injection_message
from .storage import Storage


class NewBatch(StatesGroup):
    drug_amount = State()
    drug_unit = State()
    saline_volume = State()


class RecordInjection(StatesGroup):
    route = State()
    site = State()


def build_router(storage: Storage, standard_dose_ml: Decimal) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        storage.get_or_create_user(message.from_user.id)
        await message.answer(
            "Здравствуйте. Я помогу фиксировать введения препарата и остаток текущей партии.",
            reply_markup=main_keyboard(),
        )

    @router.message(F.text == BTN_CANCEL)
    async def cancel(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=main_keyboard())

    @router.message(F.text == BTN_NEW_BATCH)
    async def new_batch(message: Message, state: FSMContext) -> None:
        await state.set_state(NewBatch.drug_amount)
        await message.answer("Введите количество препарата числом:", reply_markup=cancel_keyboard())

    @router.message(NewBatch.drug_amount)
    async def new_batch_amount(message: Message, state: FSMContext) -> None:
        try:
            amount = parse_positive_decimal(message.text or "", "Количество препарата")
        except DomainError as exc:
            await message.answer(str(exc))
            return
        await state.update_data(drug_amount=str(amount))
        await state.set_state(NewBatch.drug_unit)
        await message.answer("Введите единицу количества препарата, например мг, мкг или ЕД:")

    @router.message(NewBatch.drug_unit)
    async def new_batch_unit(message: Message, state: FSMContext) -> None:
        try:
            unit = validate_drug_unit(message.text or "")
        except DomainError as exc:
            await message.answer(str(exc))
            return
        await state.update_data(drug_unit=unit)
        await state.set_state(NewBatch.saline_volume)
        await message.answer("Введите количество физраствора в мл:")

    @router.message(NewBatch.saline_volume)
    async def new_batch_saline(message: Message, state: FSMContext) -> None:
        try:
            saline = parse_positive_decimal(message.text or "", "Количество физраствора")
        except DomainError as exc:
            await message.answer(str(exc))
            return
        data = await state.get_data()
        batch = storage.create_batch(
            telegram_user_id=message.from_user.id,
            drug_amount=Decimal(data["drug_amount"]),
            drug_unit=data["drug_unit"],
            saline_volume_ml=saline,
        )
        await state.clear()
        await message.answer("✅ Новая партия создана.\n\n" + batch_status(batch), reply_markup=main_keyboard())

    @router.message(F.text == BTN_RECORD)
    async def record_start(message: Message, state: FSMContext) -> None:
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await message.answer("Сначала создайте новую партию.", reply_markup=main_keyboard())
            return
        try:
            ensure_enough_remaining(batch.remaining_volume_ml, standard_dose_ml)
        except DomainError as exc:
            await message.answer(str(exc), reply_markup=main_keyboard())
            return
        await state.set_state(RecordInjection.route)
        await message.answer("Выберите способ введения:", reply_markup=route_keyboard())

    @router.message(RecordInjection.route)
    async def record_route(message: Message, state: FSMContext) -> None:
        try:
            route = validate_route(message.text or "")
        except DomainError as exc:
            await message.answer(str(exc), reply_markup=route_keyboard())
            return
        await state.update_data(route=route.value)
        await state.set_state(RecordInjection.site)
        await message.answer("Выберите место введения:", reply_markup=site_keyboard(route))

    @router.message(RecordInjection.site)
    async def record_site(message: Message, state: FSMContext) -> None:
        data = await state.get_data()
        route = validate_route(data["route"])
        try:
            site = validate_site(route, message.text or "")
        except DomainError as exc:
            await message.answer(str(exc), reply_markup=site_keyboard(route))
            return
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await state.clear()
            await message.answer("Текущая партия не найдена. Создайте новую партию.", reply_markup=main_keyboard())
            return
        try:
            ensure_enough_remaining(batch.remaining_volume_ml, standard_dose_ml)
        except DomainError as exc:
            await state.clear()
            await message.answer(str(exc), reply_markup=main_keyboard())
            return
        previous = storage.get_last_injections(message.from_user.id, limit=1)
        current = storage.record_injection(message.from_user.id, batch, route, site, standard_dose_ml)
        updated_batch = storage.get_current_batch(message.from_user.id)
        await state.clear()
        await message.answer(
            saved_injection_message(current, previous[0] if previous else None, updated_batch),
            reply_markup=main_keyboard(),
        )

    @router.message(F.text == BTN_STATUS)
    async def status(message: Message) -> None:
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await message.answer("Текущей партии нет. Создайте новую партию.", reply_markup=main_keyboard())
            return
        await message.answer(batch_status(batch), reply_markup=main_keyboard())

    @router.message(F.text == BTN_LAST)
    async def last(message: Message) -> None:
        injections = storage.get_last_injections(message.from_user.id, limit=1)
        if not injections:
            await message.answer("Приёмов ещё не было.", reply_markup=main_keyboard())
            return
        await message.answer("🕘 Последний приём\n" + injection_line(injections[0]), reply_markup=main_keyboard())

    @router.message(F.text == BTN_HISTORY)
    async def history(message: Message) -> None:
        injections = storage.get_history(message.from_user.id, limit=10)
        if not injections:
            await message.answer("История пуста.", reply_markup=main_keyboard())
            return
        lines = "\n".join(f"{index}. {injection_line(item)}" for index, item in enumerate(injections, 1))
        await message.answer("📜 История последних приёмов\n" + lines, reply_markup=main_keyboard())

    @router.message()
    async def fallback(message: Message) -> None:
        await message.answer("Выберите действие кнопкой ниже.", reply_markup=main_keyboard())

    return router

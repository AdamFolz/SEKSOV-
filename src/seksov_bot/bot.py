from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile, Message

from .config import read_registration_code_from_env_file
from .domain import (
    ActiveBatchError,
    DomainError,
    ensure_enough_remaining,
    parse_positive_decimal,
    validate_drug_unit,
    validate_route,
    validate_site,
)
from .keyboards import (
    BTN_BACKUP,
    BTN_CANCEL,
    BTN_EXPORT,
    BTN_FINISH_BATCH,
    BTN_HISTORY,
    BTN_OTHER_UNIT,
    BTN_LAST,
    BTN_NEW_BATCH,
    BTN_STATUS,
    BTN_UNDO_LAST,
    cancel_keyboard,
    dose_options,
    drug_unit_keyboard,
    main_keyboard,
    record_button_text,
    route_keyboard,
    site_keyboard,
)
from .messages import batch_status, help_message, history_message, injection_details, injections_csv, saved_injection_message, undo_injection_message
from .storage import Storage


class NewBatch(StatesGroup):
    drug_amount = State()
    drug_unit = State()
    saline_volume = State()


class RecordInjection(StatesGroup):
    route = State()
    site = State()


def build_router(
    storage: Storage,
    standard_dose_ml: Decimal,
    authorized_user_ids: tuple[int, ...] = (),
    admin_user_ids: tuple[int, ...] = (),
    registration_code: str | None = None,
    web_app_url: str | None = None,
) -> Router:
    router = Router()
    dose_by_button = {record_button_text(volume): volume for volume in dose_options(standard_dose_ml)}

    def kb():
        return main_keyboard(standard_dose_ml, web_app_url=web_app_url)

    def user_profile(message: Message) -> tuple[int, str | None, str | None] | None:
        user = message.from_user
        if not user:
            return None
        return user.id, user.full_name, user.username

    def remember_user(message: Message) -> int:
        profile = user_profile(message)
        if not profile:
            raise RuntimeError("Telegram user is missing from message")
        telegram_user_id, display_name, username = profile
        return storage.get_or_create_user(
            telegram_user_id,
            display_name=display_name,
            username=username,
        )

    def current_registration_code() -> str | None:
        return read_registration_code_from_env_file() or registration_code

    async def ensure_authorized(message: Message) -> bool:
        profile = user_profile(message)
        if not profile:
            await message.answer("Не удалось определить пользователя Telegram.")
            return False
        telegram_user_id, display_name, username = profile
        active_registration_code = current_registration_code()
        if telegram_user_id in authorized_user_ids or storage.is_user_authorized(telegram_user_id):
            return True
        if not authorized_user_ids and not active_registration_code:
            return True
        if active_registration_code and (message.text or "").strip() == active_registration_code:
            storage.authorize_user(telegram_user_id, display_name=display_name, username=username)
            await message.answer("✅ Доступ открыт. Теперь можно пользоваться ботом.", reply_markup=kb())
            return True
        if active_registration_code:
            await message.answer(
                "🔐 Отправьте код доступа одним сообщением.\n"
                f"Ваш Telegram ID: `{telegram_user_id}`\n"
                "Если код только что добавили в .env, просто отправьте его ещё раз.",
                parse_mode="Markdown",
            )
            return False
        await message.answer(
            "Доступ к боту ограничен.\n"
            f"Ваш Telegram ID: `{telegram_user_id}`\n"
            "Добавьте этот ID в AUTHORIZED_TELEGRAM_USER_IDS или задайте REGISTRATION_CODE в .env.",
            parse_mode="Markdown",
        )
        return False

    @router.message(Command("id"))
    async def show_user_id(message: Message) -> None:
        profile = user_profile(message)
        if not profile:
            await message.answer("Не удалось определить пользователя Telegram.")
            return
        telegram_user_id, display_name, username = profile
        username_text = f"@{username}" if username else "—"
        await message.answer(
            "🆔 Ваш Telegram ID для доступа к боту:\n"
            f"`{telegram_user_id}`\n"
            f"Имя: {display_name or '—'}\n"
            f"Username: {username_text}",
            parse_mode="Markdown",
        )


    @router.message(Command("help"))
    async def help_command(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        await message.answer(help_message(), reply_markup=kb())

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        await state.clear()
        remember_user(message)
        await message.answer(help_message(), reply_markup=kb())

    @router.message(F.text == BTN_CANCEL)
    async def cancel(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=kb())

    @router.message(F.text == BTN_NEW_BATCH)
    async def new_batch(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        remember_user(message)
        active_batch = storage.get_current_batch(message.from_user.id)
        if active_batch:
            last = storage.get_last_injections(message.from_user.id, limit=1)
            await message.answer(
                "У вас уже есть активная партия. Новую партию можно создать только после завершения текущей.\n\n"
                + batch_status(active_batch, last[0] if last else None),
                reply_markup=kb(),
            )
            return
        await state.set_state(NewBatch.drug_amount)
        await message.answer("Введите количество препарата числом:", reply_markup=cancel_keyboard())

    @router.message(NewBatch.drug_amount)
    async def new_batch_amount(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        try:
            amount = parse_positive_decimal(message.text or "", "Количество препарата")
        except DomainError as exc:
            await message.answer(str(exc))
            return
        await state.update_data(drug_amount=str(amount))
        await state.set_state(NewBatch.drug_unit)
        await message.answer("Выберите единицу препарата:", reply_markup=drug_unit_keyboard())

    @router.message(NewBatch.drug_unit)
    async def new_batch_unit(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        raw_unit = "" if message.text == BTN_OTHER_UNIT else (message.text or "")
        try:
            unit = validate_drug_unit(raw_unit)
        except DomainError as exc:
            await message.answer("Введите единицу вручную, например мг, мкг или ЕД:", reply_markup=cancel_keyboard())
            return
        await state.update_data(drug_unit=unit)
        await state.set_state(NewBatch.saline_volume)
        await message.answer("Введите количество физраствора в мл:")

    @router.message(NewBatch.saline_volume)
    async def new_batch_saline(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        try:
            saline = parse_positive_decimal(message.text or "", "Количество физраствора")
        except DomainError as exc:
            await message.answer(str(exc))
            return
        data = await state.get_data()
        try:
            batch = storage.create_batch(
                telegram_user_id=message.from_user.id,
                drug_amount=Decimal(data["drug_amount"]),
                drug_unit=data["drug_unit"],
                saline_volume_ml=saline,
            )
        except ActiveBatchError as exc:
            await state.clear()
            await message.answer(str(exc), reply_markup=kb())
            return
        await state.clear()
        await message.answer("✅ Новая партия создана.\n\n" + batch_status(batch), reply_markup=kb())

    @router.message(lambda message: message.text in dose_by_button)
    async def record_start(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
        volume_ml = dose_by_button[message.text]
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await message.answer("Сначала создайте новую партию.", reply_markup=kb())
            return
        try:
            ensure_enough_remaining(batch.remaining_volume_ml, volume_ml)
        except DomainError as exc:
            await message.answer(
                str(exc) + "\n\nПартия остаётся активной — выберите меньший объём или завершите её вручную.",
                reply_markup=kb(),
            )
            return
        await state.update_data(volume_ml=str(volume_ml))
        await state.set_state(RecordInjection.route)
        await message.answer(f"{record_button_text(volume_ml)}. Способ введения:", reply_markup=route_keyboard())

    @router.message(RecordInjection.route)
    async def record_route(message: Message, state: FSMContext) -> None:
        if not await ensure_authorized(message):
            return
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
        if not await ensure_authorized(message):
            return
        data = await state.get_data()
        route = validate_route(data["route"])
        volume_ml = Decimal(data["volume_ml"])
        try:
            site = validate_site(route, message.text or "")
        except DomainError as exc:
            await message.answer(str(exc), reply_markup=site_keyboard(route))
            return
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await state.clear()
            await message.answer("Текущая партия не найдена. Создайте новую партию.", reply_markup=kb())
            return
        try:
            ensure_enough_remaining(batch.remaining_volume_ml, volume_ml)
        except DomainError as exc:
            await state.clear()
            await message.answer(
                str(exc) + "\n\nПартия остаётся активной — выберите меньший объём или завершите её вручную.",
                reply_markup=kb(),
            )
            return
        previous = storage.get_last_injections(message.from_user.id, limit=1)
        current = storage.record_injection(message.from_user.id, batch, route, site, volume_ml)
        updated_batch = storage.get_current_batch(message.from_user.id)
        display_batch = updated_batch or replace(
            batch,
            remaining_volume_ml=current.remaining_after_ml,
            is_current=False,
        )
        await state.clear()
        await message.answer(
            saved_injection_message(current, previous[0] if previous else None, display_batch),
            reply_markup=kb(),
        )

    @router.message(F.text == BTN_FINISH_BATCH)
    async def finish_batch(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        batch = storage.deactivate_current_batch(message.from_user.id)
        if not batch:
            await message.answer("Активной партии нет. Создайте новую партию.", reply_markup=kb())
            return
        await message.answer(
            "🏁 Текущая партия завершена. История введений сохранена, теперь можно создать новую партию.",
            reply_markup=kb(),
        )

    @router.message(F.text == BTN_STATUS)
    async def status(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        batch = storage.get_current_batch(message.from_user.id)
        if not batch:
            await message.answer("Текущей партии нет. Создайте новую партию.", reply_markup=kb())
            return
        last_injections = storage.get_last_injections(message.from_user.id, limit=1)
        await message.answer(batch_status(batch, last_injections[0] if last_injections else None), reply_markup=kb())


    @router.message(F.text == BTN_EXPORT)
    async def export_history(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        injections = storage.get_history(message.from_user.id, limit=1000)
        if not injections:
            await message.answer("История пуста — экспортировать пока нечего.", reply_markup=kb())
            return
        csv_text = injections_csv(injections)
        document = BufferedInputFile(csv_text.encode("utf-8-sig"), filename="seksov-history.csv")
        await message.answer_document(document, caption="📤 История введений в CSV", reply_markup=kb())


    @router.message(F.text == BTN_BACKUP)
    async def backup_database(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        if message.from_user.id not in admin_user_ids:
            await message.answer("💾 Бэкап доступен только администраторам из ADMIN_TELEGRAM_USER_IDS.", reply_markup=kb())
            return
        if not storage.path.exists():
            await message.answer("База данных пока не создана.", reply_markup=kb())
            return
        document = BufferedInputFile(storage.backup_bytes(), filename=storage.path.name)
        await message.answer_document(document, caption="💾 Резервная копия базы SEKSOV", reply_markup=kb())

    @router.message(F.text == BTN_UNDO_LAST)
    async def undo_last_injection(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        undone = storage.undo_last_injection(message.from_user.id)
        if not undone:
            await message.answer("Нет введений, которые можно отменить.", reply_markup=kb())
            return
        injection, batch = undone
        await message.answer(undo_injection_message(injection, batch), reply_markup=kb())

    @router.message(F.text == BTN_LAST)
    async def last(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        injections = storage.get_last_injections(message.from_user.id, limit=1)
        if not injections:
            await message.answer("Приёмов ещё не было.", reply_markup=kb())
            return
        await message.answer(injection_details(injections[0]), reply_markup=kb())

    @router.message(F.text == BTN_HISTORY)
    async def history(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        injections = storage.get_history(message.from_user.id, limit=10)
        if not injections:
            await message.answer("История пуста.", reply_markup=kb())
            return
        await message.answer(history_message(injections), reply_markup=kb())

    @router.message()
    async def fallback(message: Message) -> None:
        if not await ensure_authorized(message):
            return
        await message.answer("Выберите действие кнопкой ниже.", reply_markup=kb())

    return router

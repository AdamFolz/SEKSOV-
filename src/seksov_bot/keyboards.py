from decimal import Decimal

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from .domain import INTRAMUSCULAR_SITES, INTRAVENOUS_SITES, InjectionRoute, format_ml

BTN_NEW_BATCH = "➕ Новая партия"
BTN_STATUS = "📊 Статус"
BTN_FINISH_BATCH = "🏁 Завершить партию"
BTN_LAST = "🕘 Последний приём"
BTN_HISTORY = "📜 История"
BTN_CANCEL = "❌ Отмена"


def record_button_text(standard_dose_ml: Decimal) -> str:
    return f"✅ Зафиксировать {format_ml(standard_dose_ml)}"


def main_keyboard(standard_dose_ml: Decimal) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=record_button_text(standard_dose_ml)), KeyboardButton(text=BTN_STATUS)],
            [KeyboardButton(text=BTN_NEW_BATCH), KeyboardButton(text=BTN_FINISH_BATCH)],
            [KeyboardButton(text=BTN_LAST), KeyboardButton(text=BTN_HISTORY)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_CANCEL)]], resize_keyboard=True)


def route_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=InjectionRoute.INTRAMUSCULAR.value)],
            [KeyboardButton(text=InjectionRoute.INTRAVENOUS.value)],
            [KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def site_keyboard(route: InjectionRoute) -> ReplyKeyboardMarkup:
    sites = INTRAMUSCULAR_SITES if route is InjectionRoute.INTRAMUSCULAR else INTRAVENOUS_SITES
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=site)] for site in sites] + [[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )

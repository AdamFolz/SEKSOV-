from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from .domain import INTRAMUSCULAR_SITES, INTRAVENOUS_SITES, InjectionRoute

BTN_NEW_BATCH = "➕ Новая партия"
BTN_RECORD = "💉 Зафиксировать приём"
BTN_STATUS = "📊 Статус"
BTN_LAST = "🕘 Последний приём"
BTN_HISTORY = "📜 История"
BTN_CANCEL = "❌ Отмена"


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_RECORD), KeyboardButton(text=BTN_STATUS)],
            [KeyboardButton(text=BTN_NEW_BATCH)],
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

from decimal import Decimal

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from .domain import INTRAMUSCULAR_SITES, INTRAVENOUS_SITES, InjectionRoute, format_ml

BTN_NEW_BATCH = "➕ Новая партия"
BTN_STATUS = "📊 Статус"
BTN_FINISH_BATCH = "🏁 Завершить партию"
BTN_LAST = "🕘 Последний приём"
BTN_HISTORY = "📜 История"
BTN_CANCEL = "❌ Отмена"
BTN_OTHER_UNIT = "✍️ Другая"
COMMON_DRUG_UNITS = ("мг", "мкг", "ЕД", "мл")
DEFAULT_DOSE_OPTIONS_ML = (Decimal("1"), Decimal("2"), Decimal("3"))


def dose_options(standard_dose_ml: Decimal) -> tuple[Decimal, ...]:
    options = [standard_dose_ml, *DEFAULT_DOSE_OPTIONS_ML]
    unique: list[Decimal] = []
    for option in options:
        if option not in unique:
            unique.append(option)
    return tuple(unique)


def record_button_text(volume_ml: Decimal) -> str:
    return f"💉 {format_ml(volume_ml)}"


def main_keyboard(standard_dose_ml: Decimal) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=record_button_text(volume)) for volume in dose_options(standard_dose_ml)],
            [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_HISTORY)],
            [KeyboardButton(text=BTN_NEW_BATCH), KeyboardButton(text=BTN_FINISH_BATCH)],
            [KeyboardButton(text=BTN_LAST)],
        ],
        resize_keyboard=True,
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=BTN_CANCEL)]], resize_keyboard=True)


def drug_unit_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=COMMON_DRUG_UNITS[0]), KeyboardButton(text=COMMON_DRUG_UNITS[1])],
            [KeyboardButton(text=COMMON_DRUG_UNITS[2]), KeyboardButton(text=COMMON_DRUG_UNITS[3])],
            [KeyboardButton(text=BTN_OTHER_UNIT), KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


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

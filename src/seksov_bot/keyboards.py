from decimal import Decimal

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

from .domain import INTRAMUSCULAR_SITES, INTRAVENOUS_SITES, InjectionRoute, format_ml

BTN_NEW_BATCH = "➕ Новая партия"
BTN_STATUS = "📊 Статус"
BTN_FINISH_BATCH = "🏁 Завершить партию"
BTN_LAST = "🕘 Последний приём"
BTN_HISTORY = "📜 История"
BTN_EXPORT = "📤 Экспорт CSV"
BTN_BACKUP = "💾 Бэкап"
BTN_UNDO_LAST = "↩️ Отменить последнее"
BTN_WEB_APP = "✨ Красивое приложение"
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


def main_keyboard(standard_dose_ml: Decimal, web_app_url: str | None = None) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text=record_button_text(volume)) for volume in dose_options(standard_dose_ml)],
        [KeyboardButton(text=BTN_STATUS), KeyboardButton(text=BTN_HISTORY)],
        [KeyboardButton(text=BTN_EXPORT), KeyboardButton(text=BTN_LAST)],
        [KeyboardButton(text=BTN_BACKUP), KeyboardButton(text=BTN_UNDO_LAST)],
    ]
    if web_app_url:
        rows.append([KeyboardButton(text=BTN_WEB_APP, web_app=WebAppInfo(url=web_app_url))])
    rows.append([KeyboardButton(text=BTN_NEW_BATCH), KeyboardButton(text=BTN_FINISH_BATCH)])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


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

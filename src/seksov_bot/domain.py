from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import StrEnum


ML_QUANT = Decimal("0.001")


class InjectionRoute(StrEnum):
    INTRAMUSCULAR = "внутримышечно"
    INTRAVENOUS = "внутривенно"


INTRAMUSCULAR_SITES = (
    "правая нога",
    "левая нога",
    "правое плечо",
    "левое плечо",
    "правая ягодица",
    "левая ягодица",
)

INTRAVENOUS_SITES = (
    "правая ступня",
    "левая ступня",
    "правая рука",
    "левая рука",
    "правая кисть",
    "левая кисть",
)

SITES_BY_ROUTE: dict[InjectionRoute, tuple[str, ...]] = {
    InjectionRoute.INTRAMUSCULAR: INTRAMUSCULAR_SITES,
    InjectionRoute.INTRAVENOUS: INTRAVENOUS_SITES,
}


@dataclass(frozen=True)
class User:
    id: int
    telegram_user_id: int
    display_name: str | None
    username: str | None
    created_at: datetime


@dataclass(frozen=True)
class Batch:
    id: int
    user_id: int
    drug_amount: Decimal
    drug_unit: str
    saline_volume_ml: Decimal
    total_volume_ml: Decimal
    remaining_volume_ml: Decimal
    created_at: datetime
    is_current: bool


@dataclass(frozen=True)
class Injection:
    id: int
    user_id: int
    batch_id: int
    injected_at: datetime
    route: InjectionRoute
    site: str
    volume_ml: Decimal
    remaining_after_ml: Decimal | None
    is_cancelled: bool = False
    cancelled_at: datetime | None = None


class ActiveBatchError(ValueError):
    """Raised when a user tries to create a new batch before finishing the current one."""


class DomainError(ValueError):
    """Raised when user input violates medication tracking rules."""


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def parse_positive_decimal(value: str, field_name: str) -> Decimal:
    try:
        parsed = Decimal(value.replace(",", ".").strip())
        if not parsed.is_finite():
            raise InvalidOperation
        quantized = parsed.quantize(ML_QUANT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as exc:
        raise DomainError(f"{field_name}: введите число больше нуля") from exc
    if quantized <= 0:
        raise DomainError(f"{field_name}: введите число больше нуля")
    return quantized


def validate_drug_unit(unit: str) -> str:
    cleaned = unit.strip()
    if not cleaned:
        raise DomainError("Укажите единицу количества препарата")
    if len(cleaned) > 24:
        raise DomainError("Единица количества препарата слишком длинная")
    return cleaned


def validate_route(value: str) -> InjectionRoute:
    try:
        return InjectionRoute(value)
    except ValueError as exc:
        raise DomainError("Выберите допустимый способ введения") from exc


def validate_site(route: InjectionRoute, site: str) -> str:
    if site not in SITES_BY_ROUTE[route]:
        raise DomainError("Выберите место введения из списка для выбранного способа")
    return site


def ensure_enough_remaining(remaining_ml: Decimal, dose_ml: Decimal) -> None:
    if remaining_ml < dose_ml:
        raise DomainError(
            f"В текущей партии осталось {format_ml(remaining_ml)}, "
            f"а стандартный объём введения — {format_ml(dose_ml)}. Создайте новую партию."
        )


def format_ml(value: Decimal) -> str:
    normalized = value.quantize(ML_QUANT, rounding=ROUND_HALF_UP).normalize()
    return f"{normalized} мл"


def format_dt(value: datetime) -> str:
    return value.astimezone().strftime("%d.%m.%Y %H:%M")

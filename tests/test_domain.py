from decimal import Decimal

import pytest

from seksov_bot.domain import (
    DomainError,
    InjectionRoute,
    ensure_enough_remaining,
    parse_positive_decimal,
    validate_site,
)


def test_parse_positive_decimal_accepts_comma() -> None:
    assert parse_positive_decimal("2,5", "dose") == Decimal("2.500")


def test_validate_site_depends_on_route() -> None:
    assert validate_site(InjectionRoute.INTRAMUSCULAR, "правая нога") == "правая нога"
    with pytest.raises(DomainError):
        validate_site(InjectionRoute.INTRAMUSCULAR, "правая кисть")


def test_ensure_enough_remaining_blocks_overdraft() -> None:
    ensure_enough_remaining(Decimal("1.0"), Decimal("1.0"))
    with pytest.raises(DomainError):
        ensure_enough_remaining(Decimal("0.5"), Decimal("1.0"))


@pytest.mark.parametrize("raw_value", ["NaN", "Infinity", "-Infinity"])
def test_parse_positive_decimal_rejects_non_finite_values(raw_value: str) -> None:
    with pytest.raises(DomainError):
        parse_positive_decimal(raw_value, "dose")


@pytest.mark.parametrize("raw_value", ["0.0004", "0,0004"])
def test_parse_positive_decimal_rejects_values_that_round_to_zero(raw_value: str) -> None:
    with pytest.raises(DomainError):
        parse_positive_decimal(raw_value, "dose")

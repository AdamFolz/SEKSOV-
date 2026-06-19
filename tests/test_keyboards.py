from decimal import Decimal

from seksov_bot.keyboards import record_button_text


def test_record_button_uses_configured_standard_dose() -> None:
    assert record_button_text(Decimal("1.0")) == "✅ Зафиксировать 1 мл"
    assert record_button_text(Decimal("0.5")) == "✅ Зафиксировать 0.5 мл"

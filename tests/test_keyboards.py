from decimal import Decimal

from seksov_bot.keyboards import BTN_FINISH_BATCH, main_keyboard, record_button_text


def test_record_button_uses_configured_standard_dose() -> None:
    assert record_button_text(Decimal("1.0")) == "✅ Зафиксировать 1 мл"
    assert record_button_text(Decimal("0.5")) == "✅ Зафиксировать 0.5 мл"


def test_main_keyboard_contains_manual_finish_batch_action() -> None:
    keyboard = main_keyboard(Decimal("1.0"))
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    assert BTN_FINISH_BATCH in button_texts

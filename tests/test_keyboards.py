from decimal import Decimal

from seksov_bot.keyboards import (
    BTN_FINISH_BATCH,
    COMMON_DRUG_UNITS,
    dose_options,
    drug_unit_keyboard,
    main_keyboard,
    record_button_text,
)


def test_record_buttons_include_one_two_three_ml_options() -> None:
    keyboard = main_keyboard(Decimal("1.0"))
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    assert record_button_text(Decimal("1")) == "💉 1 мл"
    assert "💉 1 мл" in button_texts
    assert "💉 2 мл" in button_texts
    assert "💉 3 мл" in button_texts


def test_dose_options_include_custom_standard_dose_without_duplicates() -> None:
    assert dose_options(Decimal("0.5")) == (Decimal("0.5"), Decimal("1"), Decimal("2"), Decimal("3"))
    assert dose_options(Decimal("2")) == (Decimal("2"), Decimal("1"), Decimal("3"))


def test_main_keyboard_contains_manual_finish_batch_action() -> None:
    keyboard = main_keyboard(Decimal("1.0"))
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    assert BTN_FINISH_BATCH in button_texts


def test_drug_unit_keyboard_contains_common_units() -> None:
    keyboard = drug_unit_keyboard()
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    for unit in COMMON_DRUG_UNITS:
        assert unit in button_texts


def test_main_keyboard_contains_export_action() -> None:
    keyboard = main_keyboard(Decimal("1.0"))
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    assert BTN_EXPORT in button_texts


def test_main_keyboard_can_include_telegram_mini_app_button() -> None:
    from seksov_bot.keyboards import BTN_WEB_APP

    keyboard = main_keyboard(Decimal("1.0"), web_app_url="https://example.com/app")
    buttons = [button for row in keyboard.keyboard for button in row]
    web_button = next(button for button in buttons if button.text == BTN_WEB_APP)

    assert web_button.web_app is not None
    assert str(web_button.web_app.url) == "https://example.com/app"


def test_main_keyboard_contains_safety_actions() -> None:
    from seksov_bot.keyboards import BTN_BACKUP, BTN_UNDO_LAST

    keyboard = main_keyboard(Decimal("1.0"))
    button_texts = [button.text for row in keyboard.keyboard for button in row]

    assert BTN_BACKUP in button_texts
    assert BTN_UNDO_LAST in button_texts

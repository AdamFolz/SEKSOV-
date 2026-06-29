import pytest

from seksov_bot.config import parse_authorized_user_ids, validate_bot_token


def test_validate_bot_token_rejects_empty_or_placeholder_values() -> None:
    for token in ("", "123456:replace_me", "123456:change_me"):
        with pytest.raises(RuntimeError):
            validate_bot_token(token)


def test_validate_bot_token_requires_telegram_separator() -> None:
    with pytest.raises(RuntimeError):
        validate_bot_token("not-a-real-token")


def test_validate_bot_token_accepts_configured_token() -> None:
    assert validate_bot_token(" 123:token ") == "123:token"


def test_parse_authorized_user_ids_accepts_empty_value() -> None:
    assert parse_authorized_user_ids("") == ()
    assert parse_authorized_user_ids("  ") == ()


def test_parse_authorized_user_ids_accepts_comma_separated_ids() -> None:
    assert parse_authorized_user_ids("123, 456,,789") == (123, 456, 789)


def test_parse_authorized_user_ids_rejects_invalid_values() -> None:
    with pytest.raises(RuntimeError):
        parse_authorized_user_ids("123,abc")


def test_settings_support_registration_code(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("REGISTRATION_CODE", "family-code")

    from seksov_bot.config import load_settings

    settings = load_settings()

    assert settings.registration_code == "family-code"


def test_read_registration_code_from_env_file(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("REGISTRATION_CODE= family123 \n", encoding="utf-8")

    from seksov_bot.config import read_registration_code_from_env_file

    assert read_registration_code_from_env_file(env_file) == "family123"


def test_read_registration_code_from_env_file_returns_none_for_missing_value(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("BOT_TOKEN=123\n", encoding="utf-8")

    from seksov_bot.config import read_registration_code_from_env_file

    assert read_registration_code_from_env_file(env_file) is None


def test_settings_support_mini_app_options(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("WEB_APP_URL", "https://example.com/app")
    monkeypatch.setenv("WEB_HOST", "127.0.0.1")
    monkeypatch.setenv("WEB_PORT", "8080")
    monkeypatch.setenv("WEB_DEV_MODE", "true")

    from seksov_bot.config import load_settings

    settings = load_settings()

    assert settings.web_app_url == "https://example.com/app"
    assert settings.web_host == "127.0.0.1"
    assert settings.web_port == 8080
    assert settings.web_dev_mode is True


def test_settings_support_admin_user_ids(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("ADMIN_TELEGRAM_USER_IDS", "100,200")

    from seksov_bot.config import load_settings

    settings = load_settings()

    assert settings.admin_telegram_user_ids == (100, 200)


def test_web_dev_mode_is_limited_to_local_host(monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("WEB_DEV_MODE", "1")
    monkeypatch.setenv("WEB_HOST", "0.0.0.0")

    from seksov_bot.config import load_settings

    with pytest.raises(RuntimeError):
        load_settings()

import pytest

from seksov_bot.config import parse_authorized_user_ids


def test_parse_authorized_user_ids_accepts_empty_value() -> None:
    assert parse_authorized_user_ids("") == ()
    assert parse_authorized_user_ids("  ") == ()


def test_parse_authorized_user_ids_accepts_comma_separated_ids() -> None:
    assert parse_authorized_user_ids("123, 456,,789") == (123, 456, 789)


def test_parse_authorized_user_ids_rejects_invalid_values() -> None:
    with pytest.raises(RuntimeError):
        parse_authorized_user_ids("123,abc")

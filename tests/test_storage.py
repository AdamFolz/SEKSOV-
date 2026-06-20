from decimal import Decimal

import pytest

from seksov_bot.domain import ActiveBatchError, InjectionRoute
from seksov_bot.storage import Storage


def test_users_have_isolated_current_batches_and_history(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    first_batch = storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("5"),
    )
    second_batch = storage.create_batch(
        telegram_user_id=200,
        drug_amount=Decimal("20"),
        drug_unit="мг",
        saline_volume_ml=Decimal("3"),
    )

    injection = storage.record_injection(
        100,
        first_batch,
        InjectionRoute.INTRAMUSCULAR,
        "правая нога",
        Decimal("1"),
    )

    assert injection.remaining_after_ml == Decimal("4")
    assert storage.get_current_batch(100).remaining_volume_ml == Decimal("4")
    assert storage.get_current_batch(200).remaining_volume_ml == Decimal("3")
    assert storage.get_history(100)[0].remaining_after_ml == Decimal("4")
    assert storage.get_history(200) == []
    assert second_batch.user_id != first_batch.user_id

    storage.close()


def test_new_batch_is_blocked_while_user_has_active_batch(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("5"),
    )

    with pytest.raises(ActiveBatchError):
        storage.create_batch(
            telegram_user_id=100,
            drug_amount=Decimal("10"),
            drug_unit="мг",
            saline_volume_ml=Decimal("2"),
        )

    assert storage.get_current_batch(100).remaining_volume_ml == Decimal("5")
    storage.close()


def test_depleted_batch_becomes_inactive_and_allows_new_batch(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    old_batch = storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("1"),
    )
    storage.record_injection(
        100,
        old_batch,
        InjectionRoute.INTRAMUSCULAR,
        "правая нога",
        Decimal("1"),
    )

    assert storage.get_current_batch(100) is None

    new_batch = storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("2"),
    )
    assert storage.get_current_batch(100).id == new_batch.id

    storage.close()


def test_user_profile_is_updated_from_telegram_metadata(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    user_id = storage.get_or_create_user(100, display_name="Ivan", username="ivan")
    row = storage.connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    assert row["display_name"] == "Ivan"
    assert row["username"] == "ivan"
    storage.close()


def test_deactivate_current_batch_allows_new_batch_for_unusable_leftover(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    old_batch = storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("0.5"),
    )

    deactivated = storage.deactivate_current_batch(100)
    assert deactivated.id == old_batch.id
    assert deactivated.is_current is False
    assert storage.get_current_batch(100) is None

    new_batch = storage.create_batch(
        telegram_user_id=100,
        drug_amount=Decimal("10"),
        drug_unit="мг",
        saline_volume_ml=Decimal("2"),
    )
    assert storage.get_current_batch(100).id == new_batch.id
    storage.close()


def test_user_authorization_can_be_persisted(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    assert storage.is_user_authorized(100) is False
    user_id = storage.authorize_user(100, display_name="Ivan", username="ivan")

    row = storage.connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    assert storage.is_user_authorized(100) is True
    assert row["display_name"] == "Ivan"
    assert row["username"] == "ivan"
    storage.close()

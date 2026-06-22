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


def test_storage_exposes_user_profile_and_batches(tmp_path) -> None:
    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    try:
        storage.authorize_user(42, display_name="Ivan", username="ivan")
        storage.create_batch(42, Decimal("100"), "мг", Decimal("5"))

        profile = storage.get_user_profile(42)
        batches = storage.get_user_batches(42)

        assert profile is not None
        assert profile["display_name"] == "Ivan"
        assert profile["is_authorized"] is True
        assert len(batches) == 1
        assert batches[0].remaining_volume_ml == Decimal("5")
    finally:
        storage.close()


def test_undo_last_injection_restores_remaining_and_hides_record_from_history(tmp_path) -> None:
    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    try:
        batch = storage.create_batch(42, Decimal("100"), "мг", Decimal("5"))
        storage.record_injection(42, batch, InjectionRoute.INTRAMUSCULAR, "правая нога", Decimal("2"))

        undone = storage.undo_last_injection(42)

        assert undone is not None
        injection, restored_batch = undone
        assert injection.volume_ml == Decimal("2")
        assert restored_batch.remaining_volume_ml == Decimal("5")
        assert storage.get_history(42) == []
    finally:
        storage.close()


def test_undo_last_injection_returns_none_when_history_is_empty(tmp_path) -> None:
    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    try:
        assert storage.undo_last_injection(42) is None
    finally:
        storage.close()


def test_migrate_adds_new_columns_to_existing_schema(tmp_path) -> None:
    db_path = tmp_path / "old.sqlite3"
    import sqlite3

    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );
        CREATE TABLE batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            drug_amount DECIMAL NOT NULL,
            drug_unit TEXT NOT NULL,
            saline_volume_ml DECIMAL NOT NULL,
            total_volume_ml DECIMAL NOT NULL,
            remaining_volume_ml DECIMAL NOT NULL,
            created_at TEXT NOT NULL,
            is_current INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE injections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
            injected_at TEXT NOT NULL,
            route TEXT NOT NULL,
            site TEXT NOT NULL,
            volume_ml DECIMAL NOT NULL
        );
        """
    )
    connection.close()

    storage = Storage(db_path)
    storage.migrate()
    try:
        user_columns = {row["name"] for row in storage.connection.execute("PRAGMA table_info(users)")}
        injection_columns = {row["name"] for row in storage.connection.execute("PRAGMA table_info(injections)")}

        assert {"display_name", "username", "is_authorized"} <= user_columns
        assert {"remaining_after_ml", "is_cancelled", "cancelled_at"} <= injection_columns
    finally:
        storage.close()


def test_backup_bytes_returns_sqlite_snapshot(tmp_path) -> None:
    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    try:
        storage.authorize_user(42, display_name="Ivan", username="ivan")

        snapshot = storage.backup_bytes()

        assert snapshot.startswith(b"SQLite format 3")
    finally:
        storage.close()


def test_record_injection_rereads_current_batch_before_subtracting(tmp_path) -> None:
    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    try:
        batch = storage.create_batch(42, Decimal("100"), "мг", Decimal("5"))

        first = storage.record_injection(42, batch, InjectionRoute.INTRAMUSCULAR, "правая нога", Decimal("1"))
        second = storage.record_injection(42, batch, InjectionRoute.INTRAMUSCULAR, "левая нога", Decimal("1"))

        assert first.remaining_after_ml == Decimal("4")
        assert second.remaining_after_ml == Decimal("3")
        assert storage.get_current_batch(42).remaining_volume_ml == Decimal("3")
    finally:
        storage.close()

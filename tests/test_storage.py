from decimal import Decimal

from seksov_bot.domain import InjectionRoute
from seksov_bot.storage import Storage


def test_users_have_isolated_current_batches_and_history(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    first_batch = storage.create_batch(telegram_user_id=100, drug_amount=Decimal("10"), drug_unit="мг", saline_volume_ml=Decimal("5"))
    second_batch = storage.create_batch(telegram_user_id=200, drug_amount=Decimal("20"), drug_unit="мг", saline_volume_ml=Decimal("3"))

    storage.record_injection(100, first_batch, InjectionRoute.INTRAMUSCULAR, "правая нога", Decimal("1"))

    assert storage.get_current_batch(100).remaining_volume_ml == Decimal("4")
    assert storage.get_current_batch(200).remaining_volume_ml == Decimal("3")
    assert len(storage.get_history(100)) == 1
    assert storage.get_history(200) == []
    assert second_batch.user_id != first_batch.user_id

    storage.close()


def test_new_batch_replaces_current_batch_for_same_user(tmp_path) -> None:
    storage = Storage(tmp_path / "bot.sqlite3")
    storage.migrate()

    storage.create_batch(telegram_user_id=100, drug_amount=Decimal("10"), drug_unit="мг", saline_volume_ml=Decimal("5"))
    new_batch = storage.create_batch(telegram_user_id=100, drug_amount=Decimal("10"), drug_unit="мг", saline_volume_ml=Decimal("2"))

    current = storage.get_current_batch(100)
    assert current.id == new_batch.id
    assert current.remaining_volume_ml == Decimal("2")

    storage.close()

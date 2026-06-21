from datetime import datetime, timezone
from decimal import Decimal

from seksov_bot.domain import Batch, Injection, InjectionRoute
from seksov_bot.messages import help_message, history_message, injection_details, injections_csv


def make_injection(index: int, volume: str, remaining: str) -> Injection:
    return Injection(
        id=index,
        user_id=1,
        batch_id=1,
        injected_at=datetime(2026, 1, index, 10, 30, tzinfo=timezone.utc),
        route=InjectionRoute.INTRAMUSCULAR,
        site="правая нога",
        volume_ml=Decimal(volume),
        remaining_after_ml=Decimal(remaining),
    )


def test_history_message_is_compact_and_numbered() -> None:
    message = history_message([make_injection(1, "1", "4"), make_injection(2, "2", "2")])

    assert message.startswith("📜 История")
    assert "1. " in message
    assert "2. " in message
    assert "💉" not in message
    assert "остаток 2 мл" in message


def test_injection_details_uses_single_compact_line() -> None:
    message = injection_details(make_injection(1, "3", "1"))

    assert message.startswith("🕘 Последний приём")
    assert "3 мл" in message
    assert "остаток 1 мл" in message


def test_injections_csv_contains_machine_readable_history() -> None:
    csv_text = injections_csv([make_injection(1, "2", "3")])

    assert "injected_at,volume_ml,route,site,remaining_after_ml,batch_id" in csv_text
    assert "2,внутримышечно,правая нога,3,1" in csv_text


def test_help_message_mentions_core_actions() -> None:
    message = help_message()

    assert "Новая партия" in message
    assert "Экспорт CSV" in message
    assert "/id" in message


def test_undo_injection_message_is_compact() -> None:
    from seksov_bot.messages import undo_injection_message

    injection = make_injection(1, "1", "4")
    batch = Batch(
        id=1,
        user_id=1,
        drug_amount=Decimal("100"),
        drug_unit="мг",
        saline_volume_ml=Decimal("5"),
        total_volume_ml=Decimal("5"),
        remaining_volume_ml=Decimal("5"),
        created_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        is_current=True,
    )

    text = undo_injection_message(injection, batch)

    assert "Последняя запись отменена" in text
    assert "Остаток восстановлен" in text

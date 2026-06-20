from datetime import datetime, timezone
from decimal import Decimal

from seksov_bot.domain import Injection, InjectionRoute
from seksov_bot.messages import history_message, injection_details


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

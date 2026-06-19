from __future__ import annotations

from .domain import Batch, Injection, format_dt, format_ml


def batch_status(batch: Batch) -> str:
    return (
        "📊 Текущая партия\n"
        f"Создана: {format_dt(batch.created_at)}\n"
        f"Препарат: {batch.drug_amount.normalize()} {batch.drug_unit}\n"
        f"Физраствор: {format_ml(batch.saline_volume_ml)}\n"
        f"Остаток: {format_ml(batch.remaining_volume_ml)} из {format_ml(batch.total_volume_ml)}"
    )


def injection_line(injection: Injection) -> str:
    return (
        f"{format_dt(injection.injected_at)} — {injection.route.value}, "
        f"{injection.site}, {format_ml(injection.volume_ml)}"
    )


def saved_injection_message(current: Injection, previous: Injection | None, batch: Batch) -> str:
    previous_text = injection_line(previous) if previous else "предыдущих приёмов не было"
    return (
        "✅ Приём сохранён\n\n"
        f"Текущий приём: {injection_line(current)}\n"
        f"Предыдущий приём: {previous_text}\n\n"
        f"Остаток в текущей партии: {format_ml(batch.remaining_volume_ml)} "
        f"из {format_ml(batch.total_volume_ml)}"
    )

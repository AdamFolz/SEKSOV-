from __future__ import annotations

from .domain import Batch, Injection, format_dt, format_ml


def batch_status(batch: Batch, last_injection: Injection | None = None) -> str:
    last_text = injection_line(last_injection) if last_injection else "приёмов ещё не было"
    return (
        "📊 Текущая партия\n"
        f"Создана: {format_dt(batch.created_at)}\n"
        f"Препарат: {batch.drug_amount.normalize()} {batch.drug_unit}\n"
        f"Исходный объём: {format_ml(batch.total_volume_ml)}\n"
        f"Физраствор: {format_ml(batch.saline_volume_ml)}\n"
        f"Текущий остаток: {format_ml(batch.remaining_volume_ml)} из {format_ml(batch.total_volume_ml)}\n"
        f"Последний приём: {last_text}"
    )


def injection_line(injection: Injection) -> str:
    remaining = (
        f", остаток после введения: {format_ml(injection.remaining_after_ml)}"
        if injection.remaining_after_ml is not None
        else ""
    )
    return (
        f"{format_dt(injection.injected_at)} — {injection.route.value}, "
        f"{injection.site}, {format_ml(injection.volume_ml)}{remaining}"
    )


def injection_details(injection: Injection) -> str:
    remaining = (
        f"\nОстаток после введения: {format_ml(injection.remaining_after_ml)}"
        if injection.remaining_after_ml is not None
        else ""
    )
    return (
        f"Дата и время: {format_dt(injection.injected_at)}\n"
        f"Способ введения: {injection.route.value}\n"
        f"Место введения: {injection.site}\n"
        f"Объём введения: {format_ml(injection.volume_ml)}"
        f"{remaining}"
    )


def saved_injection_message(current: Injection, previous: Injection | None, batch: Batch) -> str:
    previous_text = format_dt(previous.injected_at) if previous else "предыдущих приёмов не было"
    return (
        "✅ Приём сохранён\n\n"
        f"Текущий приём: {format_dt(current.injected_at)}\n"
        f"Предыдущий приём: {previous_text}\n"
        f"Способ введения: {current.route.value}\n"
        f"Место введения: {current.site}\n\n"
        f"Остаток в текущей партии: {format_ml(batch.remaining_volume_ml)} "
        f"из {format_ml(batch.total_volume_ml)}"
    )

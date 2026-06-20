from __future__ import annotations

from .domain import Batch, Injection, format_dt, format_ml


def batch_status(batch: Batch, last_injection: Injection | None = None) -> str:
    last_text = format_dt(last_injection.injected_at) if last_injection else "нет"
    return (
        "📊 Статус\n"
        f"Партия: {format_ml(batch.remaining_volume_ml)} / {format_ml(batch.total_volume_ml)}\n"
        f"Создана: {format_dt(batch.created_at)}\n"
        f"Препарат: {batch.drug_amount.normalize()} {batch.drug_unit}\n"
        f"Последний: {last_text}"
    )


def injection_line(injection: Injection) -> str:
    remaining = format_ml(injection.remaining_after_ml) if injection.remaining_after_ml is not None else "—"
    return (
        f"{format_dt(injection.injected_at)} | {format_ml(injection.volume_ml)} | "
        f"{injection.route.value}, {injection.site} | остаток {remaining}"
    )


def injection_details(injection: Injection) -> str:
    return "🕘 Последний приём\n" + injection_line(injection)


def history_message(injections: list[Injection]) -> str:
    lines = [f"{index}. {injection_line(item)}" for index, item in enumerate(injections, 1)]
    return "📜 История\n" + "\n".join(lines)


def saved_injection_message(current: Injection, previous: Injection | None, batch: Batch) -> str:
    previous_text = format_dt(previous.injected_at) if previous else "нет"
    return (
        "✅ Сохранено\n"
        f"Сейчас: {format_dt(current.injected_at)}\n"
        f"Предыдущий: {previous_text}\n"
        f"Введение: {format_ml(current.volume_ml)}, {current.route.value}, {current.site}\n"
        f"Остаток: {format_ml(batch.remaining_volume_ml)} / {format_ml(batch.total_volume_ml)}"
    )

from __future__ import annotations

import csv
from io import StringIO

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


def injections_csv(injections: list[Injection]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "injected_at",
        "volume_ml",
        "route",
        "site",
        "remaining_after_ml",
        "batch_id",
    ])
    for injection in injections:
        writer.writerow([
            injection.injected_at.isoformat(),
            str(injection.volume_ml.normalize()),
            injection.route.value,
            injection.site,
            str(injection.remaining_after_ml.normalize()) if injection.remaining_after_ml is not None else "",
            injection.batch_id,
        ])
    return output.getvalue()


def help_message() -> str:
    return (
        "ℹ️ Как пользоваться ботом\n"
        "1. Создайте партию: ➕ Новая партия.\n"
        "2. Фиксируйте введение: 💉 1/2/3 мл.\n"
        "3. Смотрите остаток: 📊 Статус.\n"
        "4. История: 📜 История или 📤 Экспорт CSV.\n"
        "5. Ошиблись: ↩️ Отменить последнее.\n"
        "6. Резервная копия: 💾 Бэкап.\n"
        "Команда /id показывает Telegram ID для доступа."
    )


def undo_injection_message(injection: Injection, batch: Batch) -> str:
    return (
        "↩️ Последняя запись отменена\n"
        f"Отменено: {format_dt(injection.injected_at)} · {format_ml(injection.volume_ml)} · "
        f"{injection.route.value}, {injection.site}\n"
        f"Остаток восстановлен: {format_ml(batch.remaining_volume_ml)} / {format_ml(batch.total_volume_ml)}"
    )

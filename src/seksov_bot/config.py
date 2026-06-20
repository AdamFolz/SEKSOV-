from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from .domain import DomainError, parse_positive_decimal


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: Path
    standard_dose_ml: Decimal
    authorized_telegram_user_ids: tuple[int, ...]
    registration_code: str | None


def parse_authorized_user_ids(raw_value: str) -> tuple[int, ...]:
    cleaned = raw_value.strip()
    if not cleaned:
        return ()
    user_ids: list[int] = []
    for item in cleaned.split(","):
        candidate = item.strip()
        if not candidate:
            continue
        try:
            user_ids.append(int(candidate))
        except ValueError as exc:
            raise RuntimeError("AUTHORIZED_TELEGRAM_USER_IDS must contain only comma-separated integers") from exc
    return tuple(user_ids)


def load_settings() -> Settings:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    database_path = Path(os.getenv("DATABASE_PATH", "data/seksov.sqlite3"))
    try:
        dose = parse_positive_decimal(os.getenv("STANDARD_DOSE_ML", "1.0"), "STANDARD_DOSE_ML")
    except DomainError as exc:
        raise RuntimeError(str(exc)) from exc
    authorized_user_ids = parse_authorized_user_ids(os.getenv("AUTHORIZED_TELEGRAM_USER_IDS", ""))
    registration_code = os.getenv("REGISTRATION_CODE", "").strip() or None
    return Settings(
        bot_token=token,
        database_path=database_path,
        standard_dose_ml=dose,
        authorized_telegram_user_ids=authorized_user_ids,
        registration_code=registration_code,
    )

from __future__ import annotations

import os

from dotenv import load_dotenv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from .domain import DomainError, parse_positive_decimal


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: Path
    standard_dose_ml: Decimal


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
    return Settings(bot_token=token, database_path=database_path, standard_dose_ml=dose)

from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from dotenv import dotenv_values, load_dotenv

from .domain import DomainError, parse_positive_decimal


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: Path
    standard_dose_ml: Decimal
    authorized_telegram_user_ids: tuple[int, ...]
    admin_telegram_user_ids: tuple[int, ...]
    registration_code: str | None
    web_app_url: str | None
    web_host: str
    web_port: int
    web_dev_mode: bool


def validate_bot_token(raw_value: str) -> str:
    token = raw_value.strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required")
    if "replace_me" in token.lower() or "change_me" in token.lower():
        raise RuntimeError("BOT_TOKEN must be replaced with the real token from BotFather")
    if ":" not in token:
        raise RuntimeError("BOT_TOKEN must look like a Telegram bot token from BotFather")
    return token


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


def parse_bool(raw_value: str) -> bool:
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def read_registration_code_from_env_file(path: Path | str = ".env") -> str | None:
    values = dotenv_values(path)
    value = values.get("REGISTRATION_CODE")
    return value.strip() if value and value.strip() else None


def load_settings() -> Settings:
    load_dotenv()
    token = validate_bot_token(os.getenv("BOT_TOKEN", ""))
    database_path = Path(os.getenv("DATABASE_PATH", "data/seksov.sqlite3"))
    try:
        dose = parse_positive_decimal(os.getenv("STANDARD_DOSE_ML", "1.0"), "STANDARD_DOSE_ML")
    except DomainError as exc:
        raise RuntimeError(str(exc)) from exc
    authorized_user_ids = parse_authorized_user_ids(os.getenv("AUTHORIZED_TELEGRAM_USER_IDS", ""))
    admin_user_ids = parse_authorized_user_ids(os.getenv("ADMIN_TELEGRAM_USER_IDS", ""))
    registration_code = os.getenv("REGISTRATION_CODE", "").strip() or None
    web_app_url = os.getenv("WEB_APP_URL", "").strip() or None
    web_host = os.getenv("WEB_HOST", "127.0.0.1").strip() or "127.0.0.1"
    try:
        web_port = int(os.getenv("WEB_PORT", "8000"))
    except ValueError as exc:
        raise RuntimeError("WEB_PORT must be an integer") from exc
    web_dev_mode = parse_bool(os.getenv("WEB_DEV_MODE", "0"))
    if web_dev_mode and web_host not in {"127.0.0.1", "localhost", "::1"}:
        raise RuntimeError("WEB_DEV_MODE can only be enabled with WEB_HOST=127.0.0.1, localhost, or ::1")
    return Settings(
        bot_token=token,
        database_path=database_path,
        standard_dose_ml=dose,
        authorized_telegram_user_ids=authorized_user_ids,
        admin_telegram_user_ids=admin_user_ids,
        registration_code=registration_code,
        web_app_url=web_app_url,
        web_host=web_host,
        web_port=web_port,
        web_dev_mode=web_dev_mode,
    )

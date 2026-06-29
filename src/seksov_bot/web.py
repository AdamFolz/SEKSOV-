from __future__ import annotations

import hashlib
import hmac
import json
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import load_settings
from .domain import Batch, Injection, format_dt, format_ml
from .storage import Storage

STATIC_DIR = Path(__file__).with_name("web_static")
INIT_DATA_MAX_AGE_SECONDS = 24 * 60 * 60


def validate_telegram_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = INIT_DATA_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing Telegram WebApp hash")
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid Telegram WebApp signature")
    auth_date_raw = parsed.get("auth_date")
    if not auth_date_raw:
        raise ValueError("Telegram WebApp auth_date is missing")
    try:
        auth_date = int(auth_date_raw)
    except ValueError as exc:
        raise ValueError("Telegram WebApp auth_date is invalid") from exc
    now = int(time.time())
    if auth_date > now + 60:
        raise ValueError("Telegram WebApp auth_date is in the future")
    if now - auth_date > max_age_seconds:
        raise ValueError("Telegram WebApp init data is expired")
    user_raw = parsed.get("user")
    if not user_raw:
        raise ValueError("Telegram WebApp user is missing")
    parsed["user"] = json.loads(user_raw)
    return parsed


def _batch_payload(batch: Batch | None) -> dict[str, Any] | None:
    if not batch:
        return None
    percent = 0
    if batch.total_volume_ml > 0:
        percent = int((batch.remaining_volume_ml / batch.total_volume_ml * 100).to_integral_value())
    return {
        "id": batch.id,
        "drugAmount": str(batch.drug_amount.normalize()),
        "drugUnit": batch.drug_unit,
        "createdAt": format_dt(batch.created_at),
        "remainingMl": format_ml(batch.remaining_volume_ml),
        "totalMl": format_ml(batch.total_volume_ml),
        "remainingPercent": max(0, min(100, percent)),
        "isCurrent": batch.is_current,
    }


def _injection_payload(injection: Injection) -> dict[str, Any]:
    return {
        "id": injection.id,
        "batchId": injection.batch_id,
        "injectedAt": format_dt(injection.injected_at),
        "volumeMl": format_ml(injection.volume_ml),
        "route": injection.route.value,
        "site": injection.site,
        "remainingAfterMl": format_ml(injection.remaining_after_ml) if injection.remaining_after_ml is not None else "—",
    }


def create_app(storage: Storage | None = None) -> FastAPI:
    settings = load_settings()
    owns_storage = storage is None
    app_storage = storage or Storage(settings.database_path)
    app_storage.migrate()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            if owns_storage:
                app_storage.close()

    app = FastAPI(title="SEKSOV Mini App", docs_url=None, redoc_url=None, lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    def resolve_telegram_user_id(init_data: str | None, dev_user_id: int | None) -> int:
        if init_data:
            try:
                payload = validate_telegram_init_data(init_data, settings.bot_token)
            except ValueError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            return int(payload["user"]["id"])
        if settings.web_dev_mode and dev_user_id is not None:
            return dev_user_id
        raise HTTPException(status_code=401, detail="Open this page from Telegram Mini App")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    @app.get("/api/me")
    def me(
        initData: str | None = Query(default=None),
        telegram_user_id: int | None = Query(default=None),
    ) -> dict[str, Any]:
        user_id = resolve_telegram_user_id(initData, telegram_user_id)
        profile = app_storage.get_user_profile(user_id)
        access_is_restricted = (
            bool(settings.authorized_telegram_user_ids or settings.registration_code) or not settings.web_dev_mode
        )
        if access_is_restricted and user_id not in settings.authorized_telegram_user_ids:
            if not profile or not profile["is_authorized"]:
                raise HTTPException(status_code=403, detail="User is not authorized")
        current_batch = app_storage.get_current_batch(user_id)
        history = app_storage.get_history(user_id, limit=30)
        batches = app_storage.get_user_batches(user_id, limit=10)
        return {
            "profile": {
                "telegramUserId": user_id,
                "displayName": profile["display_name"] if profile else "Гость",
                "username": profile["username"] if profile else None,
            },
            "currentBatch": _batch_payload(current_batch),
            "history": [_injection_payload(item) for item in history],
            "batches": [_batch_payload(item) for item in batches],
        }

    return app

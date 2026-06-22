import hashlib
import hmac
import json
import time
from decimal import Decimal
from urllib.parse import urlencode

from fastapi.testclient import TestClient

from seksov_bot.domain import InjectionRoute
from seksov_bot.storage import Storage


def test_mini_app_dev_api_returns_current_batch_and_history(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.setenv("WEB_DEV_MODE", "1")
    monkeypatch.delenv("AUTHORIZED_TELEGRAM_USER_IDS", raising=False)
    monkeypatch.delenv("REGISTRATION_CODE", raising=False)

    from seksov_bot.web import create_app

    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    batch = storage.create_batch(42, Decimal("100"), "мг", Decimal("5"))
    storage.record_injection(42, batch, InjectionRoute.INTRAMUSCULAR, "правая нога", Decimal("1"))

    app = create_app(storage=storage)
    client = TestClient(app)

    response = client.get("/api/me", params={"telegram_user_id": 42})

    assert response.status_code == 200
    payload = response.json()
    assert payload["currentBatch"]["remainingMl"] == "4 мл"
    assert payload["history"][0]["site"] == "правая нога"

    storage.close()


def test_mini_app_rejects_unsigned_request_when_dev_mode_disabled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "123:token")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.setenv("WEB_DEV_MODE", "0")

    from seksov_bot.web import create_app

    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    app = create_app(storage=storage)
    client = TestClient(app)

    response = client.get("/api/me", params={"telegram_user_id": 42})

    assert response.status_code == 401

    storage.close()


def test_web_module_import_does_not_require_runtime_environment(monkeypatch) -> None:
    monkeypatch.delenv("BOT_TOKEN", raising=False)

    import importlib
    import seksov_bot.web as web_module

    reloaded = importlib.reload(web_module)

    assert callable(reloaded.create_app)


def signed_init_data(bot_token: str, user_id: int, auth_date: int | None = None) -> str:
    payload = {
        "auth_date": str(auth_date or int(time.time())),
        "query_id": "query",
        "user": json.dumps({"id": user_id}),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(payload)


def test_mini_app_accepts_valid_signed_telegram_init_data(tmp_path, monkeypatch) -> None:
    bot_token = "123:token"
    monkeypatch.setenv("BOT_TOKEN", bot_token)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.setenv("WEB_DEV_MODE", "0")
    monkeypatch.delenv("AUTHORIZED_TELEGRAM_USER_IDS", raising=False)
    monkeypatch.delenv("REGISTRATION_CODE", raising=False)

    from seksov_bot.web import create_app

    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    app = create_app(storage=storage)
    client = TestClient(app)

    response = client.get("/api/me", params={"initData": signed_init_data(bot_token, 42)})

    assert response.status_code == 200
    assert response.json()["profile"]["telegramUserId"] == 42

    storage.close()


def test_mini_app_rejects_tampered_telegram_init_data(tmp_path, monkeypatch) -> None:
    bot_token = "123:token"
    monkeypatch.setenv("BOT_TOKEN", bot_token)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.setenv("WEB_DEV_MODE", "0")

    from seksov_bot.web import create_app

    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    app = create_app(storage=storage)
    client = TestClient(app)
    init_data = signed_init_data(bot_token, 42).replace("42", "43")

    response = client.get("/api/me", params={"initData": init_data})

    assert response.status_code == 401

    storage.close()


def test_mini_app_rejects_expired_telegram_init_data(tmp_path, monkeypatch) -> None:
    bot_token = "123:token"
    monkeypatch.setenv("BOT_TOKEN", bot_token)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "db.sqlite3"))
    monkeypatch.setenv("WEB_DEV_MODE", "0")

    from seksov_bot.web import create_app

    storage = Storage(tmp_path / "db.sqlite3")
    storage.migrate()
    app = create_app(storage=storage)
    client = TestClient(app)

    response = client.get("/api/me", params={"initData": signed_init_data(bot_token, 42, auth_date=1)})

    assert response.status_code == 401

    storage.close()

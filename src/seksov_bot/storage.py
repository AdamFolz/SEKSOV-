from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .domain import ActiveBatchError, Batch, Injection, InjectionRoute, utcnow


def _adapt_decimal(value: Decimal) -> str:
    return str(value)


def _convert_decimal(value: bytes) -> Decimal:
    return Decimal(value.decode())


sqlite3.register_adapter(Decimal, _adapt_decimal)
sqlite3.register_converter("DECIMAL", _convert_decimal)


def _dt_to_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _dt_from_text(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(timezone.utc)


class Storage:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def close(self) -> None:
        self.connection.close()

    def migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER NOT NULL UNIQUE,
                display_name TEXT,
                username TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                drug_amount DECIMAL NOT NULL,
                drug_unit TEXT NOT NULL,
                saline_volume_ml DECIMAL NOT NULL,
                total_volume_ml DECIMAL NOT NULL,
                remaining_volume_ml DECIMAL NOT NULL,
                created_at TEXT NOT NULL,
                is_current INTEGER NOT NULL DEFAULT 1
            );

            CREATE INDEX IF NOT EXISTS idx_batches_user_current
                ON batches(user_id, is_current);

            CREATE TABLE IF NOT EXISTS injections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                batch_id INTEGER NOT NULL REFERENCES batches(id) ON DELETE CASCADE,
                injected_at TEXT NOT NULL,
                route TEXT NOT NULL,
                site TEXT NOT NULL,
                volume_ml DECIMAL NOT NULL,
                remaining_after_ml DECIMAL
            );

            CREATE INDEX IF NOT EXISTS idx_injections_user_time
                ON injections(user_id, injected_at DESC, id DESC);
            """
        )
        self._ensure_column("users", "display_name", "TEXT")
        self._ensure_column("users", "username", "TEXT")
        self._ensure_column("injections", "remaining_after_ml", "DECIMAL")

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def get_or_create_user(
        self,
        telegram_user_id: int,
        display_name: str | None = None,
        username: str | None = None,
    ) -> int:
        row = self.connection.execute(
            "SELECT id FROM users WHERE telegram_user_id = ?", (telegram_user_id,)
        ).fetchone()
        if row:
            self.connection.execute(
                "UPDATE users SET display_name = COALESCE(?, display_name), username = COALESCE(?, username) WHERE id = ?",
                (display_name, username, int(row["id"])),
            )
            return int(row["id"])
        cursor = self.connection.execute(
            "INSERT INTO users (telegram_user_id, display_name, username, created_at) VALUES (?, ?, ?, ?)",
            (telegram_user_id, display_name, username, _dt_to_text(utcnow())),
        )
        return int(cursor.lastrowid)

    def create_batch(
        self,
        telegram_user_id: int,
        drug_amount: Decimal,
        drug_unit: str,
        saline_volume_ml: Decimal,
    ) -> Batch:
        user_id = self.get_or_create_user(telegram_user_id)
        existing = self.get_current_batch(telegram_user_id)
        if existing:
            raise ActiveBatchError("У вас уже есть активная партия. Сначала используйте текущую партию.")
        now = utcnow()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO batches (
                    user_id, drug_amount, drug_unit, saline_volume_ml,
                    total_volume_ml, remaining_volume_ml, created_at, is_current
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    user_id,
                    drug_amount,
                    drug_unit,
                    saline_volume_ml,
                    saline_volume_ml,
                    saline_volume_ml,
                    _dt_to_text(now),
                ),
            )
        return Batch(
            id=int(cursor.lastrowid),
            user_id=user_id,
            drug_amount=drug_amount,
            drug_unit=drug_unit,
            saline_volume_ml=saline_volume_ml,
            total_volume_ml=saline_volume_ml,
            remaining_volume_ml=saline_volume_ml,
            created_at=now,
            is_current=True,
        )

    def get_current_batch(self, telegram_user_id: int) -> Batch | None:
        user_id = self.get_or_create_user(telegram_user_id)
        row = self.connection.execute(
            """
            SELECT * FROM batches
            WHERE user_id = ? AND is_current = 1
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        return self._batch_from_row(row) if row else None

    def deactivate_current_batch(self, telegram_user_id: int) -> Batch | None:
        batch = self.get_current_batch(telegram_user_id)
        if not batch:
            return None
        self.connection.execute(
            "UPDATE batches SET is_current = 0 WHERE id = ? AND user_id = ?",
            (batch.id, batch.user_id),
        )
        return self._batch_from_row(
            self.connection.execute("SELECT * FROM batches WHERE id = ?", (batch.id,)).fetchone()
        )

    def record_injection(
        self,
        telegram_user_id: int,
        batch: Batch,
        route: InjectionRoute,
        site: str,
        volume_ml: Decimal,
    ) -> Injection:
        user_id = self.get_or_create_user(telegram_user_id)
        now = utcnow()
        with self.connection:
            remaining_after_ml = batch.remaining_volume_ml - volume_ml
            cursor = self.connection.execute(
                """
                INSERT INTO injections (
                    user_id, batch_id, injected_at, route, site, volume_ml, remaining_after_ml
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, batch.id, _dt_to_text(now), route.value, site, volume_ml, remaining_after_ml),
            )
            is_current = 0 if remaining_after_ml < volume_ml else 1
            self.connection.execute(
                "UPDATE batches SET remaining_volume_ml = ?, is_current = ? WHERE id = ? AND user_id = ?",
                (remaining_after_ml, is_current, batch.id, user_id),
            )
        return Injection(int(cursor.lastrowid), user_id, batch.id, now, route, site, volume_ml, remaining_after_ml)

    def get_last_injections(self, telegram_user_id: int, limit: int = 2) -> list[Injection]:
        user_id = self.get_or_create_user(telegram_user_id)
        rows = self.connection.execute(
            """
            SELECT * FROM injections
            WHERE user_id = ?
            ORDER BY injected_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [self._injection_from_row(row) for row in rows]

    def get_history(self, telegram_user_id: int, limit: int = 10) -> list[Injection]:
        return self.get_last_injections(telegram_user_id, limit)

    def _batch_from_row(self, row: sqlite3.Row) -> Batch:
        return Batch(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            drug_amount=Decimal(row["drug_amount"]),
            drug_unit=row["drug_unit"],
            saline_volume_ml=Decimal(row["saline_volume_ml"]),
            total_volume_ml=Decimal(row["total_volume_ml"]),
            remaining_volume_ml=Decimal(row["remaining_volume_ml"]),
            created_at=_dt_from_text(row["created_at"]),
            is_current=bool(row["is_current"]),
        )

    def _injection_from_row(self, row: sqlite3.Row) -> Injection:
        return Injection(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            batch_id=int(row["batch_id"]),
            injected_at=_dt_from_text(row["injected_at"]),
            route=InjectionRoute(row["route"]),
            site=row["site"],
            volume_ml=Decimal(row["volume_ml"]),
            remaining_after_ml=Decimal(row["remaining_after_ml"]) if row["remaining_after_ml"] is not None else None,
        )

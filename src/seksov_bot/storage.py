from __future__ import annotations

import sqlite3
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import RLock

from .domain import ActiveBatchError, Batch, DomainError, Injection, InjectionRoute, utcnow


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
        self._lock = RLock()
        self.connection = sqlite3.connect(
            self.path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 5000")
        self.connection.execute("PRAGMA journal_mode = WAL")

    def close(self) -> None:
        with self._lock:
            self.connection.close()

    def migrate(self) -> None:
        with self._lock:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_user_id INTEGER NOT NULL UNIQUE,
                    display_name TEXT,
                    username TEXT,
                    is_authorized INTEGER NOT NULL DEFAULT 0,
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
                    remaining_after_ml DECIMAL,
                    is_cancelled INTEGER NOT NULL DEFAULT 0,
                    cancelled_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_injections_user_time
                    ON injections(user_id, injected_at DESC, id DESC);
                """
            )
            self._ensure_column("users", "display_name", "TEXT")
            self._ensure_column("users", "username", "TEXT")
            self._ensure_column("users", "is_authorized", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column("injections", "remaining_after_ml", "DECIMAL")
            self._ensure_column("injections", "is_cancelled", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column("injections", "cancelled_at", "TEXT")

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in self.connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            self.connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    def backup_bytes(self) -> bytes:
        with self._lock:
            with tempfile.TemporaryDirectory() as directory:
                backup_path = Path(directory) / "backup.sqlite3"
                backup_connection = sqlite3.connect(backup_path)
                try:
                    self.connection.backup(backup_connection)
                finally:
                    backup_connection.close()
                return backup_path.read_bytes()

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

    def is_user_authorized(self, telegram_user_id: int) -> bool:
        row = self.connection.execute(
            "SELECT is_authorized FROM users WHERE telegram_user_id = ?",
            (telegram_user_id,),
        ).fetchone()
        return bool(row and row["is_authorized"])

    def authorize_user(
        self,
        telegram_user_id: int,
        display_name: str | None = None,
        username: str | None = None,
    ) -> int:
        with self._lock:
            user_id = self.get_or_create_user(telegram_user_id, display_name=display_name, username=username)
            self.connection.execute("UPDATE users SET is_authorized = 1 WHERE id = ?", (user_id,))
            return user_id

    def get_user_profile(self, telegram_user_id: int) -> dict[str, object] | None:
        row = self.connection.execute(
            """
            SELECT id, telegram_user_id, display_name, username, is_authorized, created_at
            FROM users
            WHERE telegram_user_id = ?
            """,
            (telegram_user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": int(row["id"]),
            "telegram_user_id": int(row["telegram_user_id"]),
            "display_name": row["display_name"],
            "username": row["username"],
            "is_authorized": bool(row["is_authorized"]),
            "created_at": _dt_from_text(row["created_at"]),
        }

    def get_user_batches(self, telegram_user_id: int, limit: int = 20) -> list[Batch]:
        user_id = self.get_or_create_user(telegram_user_id)
        rows = self.connection.execute(
            """
            SELECT * FROM batches
            WHERE user_id = ?
            ORDER BY is_current DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [self._batch_from_row(row) for row in rows]

    def create_batch(
        self,
        telegram_user_id: int,
        drug_amount: Decimal,
        drug_unit: str,
        saline_volume_ml: Decimal,
    ) -> Batch:
        with self._lock:
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
        with self._lock:
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
        with self._lock:
            user_id = self.get_or_create_user(telegram_user_id)
            now = utcnow()
            self.connection.execute("BEGIN IMMEDIATE")
            try:
                current_row = self.connection.execute(
                    "SELECT * FROM batches WHERE id = ? AND user_id = ? AND is_current = 1",
                    (batch.id, user_id),
                ).fetchone()
                if not current_row:
                    raise DomainError("Текущая партия не найдена. Создайте новую партию.")
                current_batch = self._batch_from_row(current_row)
                remaining_after_ml = current_batch.remaining_volume_ml - volume_ml
                if remaining_after_ml < 0:
                    raise DomainError("В текущей партии недостаточно остатка для выбранного объёма.")
                cursor = self.connection.execute(
                    """
                    INSERT INTO injections (
                        user_id, batch_id, injected_at, route, site, volume_ml, remaining_after_ml
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, batch.id, _dt_to_text(now), route.value, site, volume_ml, remaining_after_ml),
                )
                is_current = 0 if remaining_after_ml <= 0 else 1
                self.connection.execute(
                    "UPDATE batches SET remaining_volume_ml = ?, is_current = ? WHERE id = ? AND user_id = ?",
                    (remaining_after_ml, is_current, batch.id, user_id),
                )
            except Exception:
                self.connection.rollback()
                raise
            else:
                self.connection.commit()
            return Injection(int(cursor.lastrowid), user_id, batch.id, now, route, site, volume_ml, remaining_after_ml)

    def get_last_injections(self, telegram_user_id: int, limit: int = 2) -> list[Injection]:
        user_id = self.get_or_create_user(telegram_user_id)
        rows = self.connection.execute(
            """
            SELECT * FROM injections
            WHERE user_id = ? AND is_cancelled = 0
            ORDER BY injected_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
        return [self._injection_from_row(row) for row in rows]

    def get_history(self, telegram_user_id: int, limit: int = 10) -> list[Injection]:
        return self.get_last_injections(telegram_user_id, limit)

    def undo_last_injection(self, telegram_user_id: int) -> tuple[Injection, Batch] | None:
        with self._lock:
            user_id = self.get_or_create_user(telegram_user_id)
            row = self.connection.execute(
                """
                SELECT * FROM injections
                WHERE user_id = ? AND is_cancelled = 0
                ORDER BY injected_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
            if not row:
                return None
            injection = self._injection_from_row(row)
            batch_row = self.connection.execute(
                "SELECT * FROM batches WHERE id = ? AND user_id = ?",
                (injection.batch_id, user_id),
            ).fetchone()
            if not batch_row:
                return None
            batch = self._batch_from_row(batch_row)
            restored_remaining = min(batch.total_volume_ml, batch.remaining_volume_ml + injection.volume_ml)
            current_batch = self.get_current_batch(telegram_user_id)
            should_reactivate_batch = current_batch is None or current_batch.id == batch.id
            with self.connection:
                self.connection.execute(
                    "UPDATE injections SET is_cancelled = 1, cancelled_at = ? WHERE id = ? AND user_id = ?",
                    (_dt_to_text(utcnow()), injection.id, user_id),
                )
                self.connection.execute(
                    "UPDATE batches SET remaining_volume_ml = ?, is_current = ? WHERE id = ? AND user_id = ?",
                    (restored_remaining, 1 if should_reactivate_batch else batch.is_current, batch.id, user_id),
                )
            updated_batch = self._batch_from_row(
                self.connection.execute("SELECT * FROM batches WHERE id = ?", (batch.id,)).fetchone()
            )
            return injection, updated_batch

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
            is_cancelled=bool(row["is_cancelled"]) if "is_cancelled" in row.keys() else False,
            cancelled_at=_dt_from_text(row["cancelled_at"]) if "cancelled_at" in row.keys() and row["cancelled_at"] else None,
        )

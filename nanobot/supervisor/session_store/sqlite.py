"""SQLite-backed distributed session store for supervisor."""

from __future__ import annotations

from datetime import date, datetime, time as dt_time
from enum import Enum
import json
import os
from pathlib import Path
import time
from typing import Any

import aiosqlite
from loguru import logger

from nanobot.supervisor.session_store.base import DistributedSessionStore


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime, date, dt_time)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return list(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


class SQLiteDistributedSessionStore(DistributedSessionStore):
    """SQLite persistence for shared supervisor sessions."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def init(self) -> None:
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS supervisor_sessions (
                session_key TEXT PRIMARY KEY,
                updated_at REAL NOT NULL,
                payload TEXT NOT NULL
            )
            """
        )
        await self._db.commit()
        logger.debug("SQLiteDistributedSessionStore initialized at {}", self._db_path)

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None
            logger.debug("SQLiteDistributedSessionStore connection closed")

    async def get_session(self, key: str) -> dict[str, Any] | None:
        db = self._require_db()
        async with db.execute(
            "SELECT payload FROM supervisor_sessions WHERE session_key = ?",
            (key,),
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return json.loads(row["payload"])

    async def set_session(self, key: str, value: dict[str, Any]) -> None:
        db = self._require_db()
        payload = json.dumps(value, ensure_ascii=False, default=_json_default)
        await db.execute(
            """
            INSERT INTO supervisor_sessions (session_key, updated_at, payload)
            VALUES (?, ?, ?)
            ON CONFLICT(session_key) DO UPDATE SET
                updated_at = excluded.updated_at,
                payload = excluded.payload
            """,
            (key, time.time(), payload),
        )
        await db.commit()

    def _require_db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Session store not initialized. Call init() first.")
        return self._db

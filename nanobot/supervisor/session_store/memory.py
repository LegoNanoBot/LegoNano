"""In-memory distributed session store fallback."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from typing import Any

from nanobot.supervisor.session_store.base import DistributedSessionStore


class InMemoryDistributedSessionStore(DistributedSessionStore):
    """Simple process-local session store used when persistence is unavailable."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sessions: dict[str, dict[str, Any]] = {}

    async def get_session(self, key: str) -> dict[str, Any] | None:
        async with self._lock:
            payload = self._sessions.get(key)
            return deepcopy(payload) if payload is not None else None

    async def set_session(self, key: str, value: dict[str, Any]) -> None:
        async with self._lock:
            self._sessions[key] = deepcopy(value)

"""Abstract storage interface for distributed supervisor sessions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DistributedSessionStore(ABC):
    """Persistence interface for shared session payloads keyed by session key."""

    async def init(self) -> None:
        """Initialize the backing store if needed."""

    async def close(self) -> None:
        """Close any underlying resources."""

    @abstractmethod
    async def get_session(self, key: str) -> dict[str, Any] | None:
        """Fetch session payload by key."""

    @abstractmethod
    async def set_session(self, key: str, value: dict[str, Any]) -> None:
        """Upsert a session payload by key."""

"""Persistent storage backends for supervisor distributed sessions."""

from nanobot.supervisor.session_store.base import DistributedSessionStore
from nanobot.supervisor.session_store.memory import InMemoryDistributedSessionStore

try:
    from nanobot.supervisor.session_store.sqlite import SQLiteDistributedSessionStore
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    SQLiteDistributedSessionStore = None

__all__ = [
    "DistributedSessionStore",
    "InMemoryDistributedSessionStore",
    "SQLiteDistributedSessionStore",
]

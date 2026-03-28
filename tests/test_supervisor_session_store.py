"""Tests for supervisor distributed session store backends."""

import asyncio
from datetime import datetime
from enum import Enum

import pytest


@pytest.mark.asyncio
async def test_sqlite_distributed_session_store_roundtrip(tmp_path):
    pytest.importorskip("aiosqlite")

    from nanobot.supervisor.session_store import SQLiteDistributedSessionStore

    db_path = tmp_path / "supervisor.db"
    store = SQLiteDistributedSessionStore(str(db_path))
    await store.init()

    key = "cli:user-1"
    value = {
        "messages": [{"role": "user", "content": "hello"}],
        "meta": {"channel": "cli"},
    }

    await store.set_session(key, value)
    loaded = await store.get_session(key)

    assert loaded == value
    await store.close()


@pytest.mark.asyncio
async def test_sqlite_distributed_session_store_concurrent_writes_same_key(tmp_path):
    pytest.importorskip("aiosqlite")

    from nanobot.supervisor.session_store import SQLiteDistributedSessionStore

    db_path = tmp_path / "supervisor.db"
    store = SQLiteDistributedSessionStore(str(db_path))
    await store.init()

    key = "tg:1001"

    async def write_once(index: int) -> None:
        await store.set_session(
            key,
            {
                "messages": [{"role": "assistant", "content": f"m-{index}"}],
                "version": index,
            },
        )

    await asyncio.gather(*(write_once(i) for i in range(20)))

    loaded = await store.get_session(key)
    assert loaded is not None
    assert isinstance(loaded.get("messages"), list)
    assert "version" in loaded

    await store.close()


@pytest.mark.asyncio
async def test_sqlite_distributed_session_store_serializes_common_python_types(tmp_path):
    pytest.importorskip("aiosqlite")

    from nanobot.supervisor.session_store import SQLiteDistributedSessionStore

    class _Kind(Enum):
        A = "A"

    db_path = tmp_path / "supervisor.db"
    store = SQLiteDistributedSessionStore(str(db_path))
    await store.init()

    key = "cli:user-typed"
    value = {
        "kind": _Kind.A,
        "created_at": datetime(2026, 3, 28, 9, 30, 0),
        "tags": {"x", "y"},
    }

    await store.set_session(key, value)
    loaded = await store.get_session(key)

    assert loaded is not None
    assert loaded["kind"] == "A"
    assert loaded["created_at"] == "2026-03-28T09:30:00"
    assert sorted(loaded["tags"]) == ["x", "y"]

    await store.close()

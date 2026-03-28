"""Tests for worker runner resilience."""

from __future__ import annotations

from pathlib import Path

import pytest

from nanobot.worker.runner import WorkerRunner


class _DummyProvider:
    async def chat_with_retry(self, *args, **kwargs):
        raise AssertionError("chat_with_retry should not be called in these tests")


class _StubClient:
    def __init__(self, register_side_effects: list[object]) -> None:
        self._register_side_effects = list(register_side_effects)
        self.register_calls = 0
        self.unregister_calls = 0
        self.close_calls = 0

    async def register(self, name: str) -> dict:
        self.register_calls += 1
        item = self._register_side_effects.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def unregister(self) -> None:
        self.unregister_calls += 1

    async def close(self) -> None:
        self.close_calls += 1


@pytest.mark.asyncio
async def test_runner_retries_registration_until_success(tmp_path: Path, monkeypatch):
    client = _StubClient([
        RuntimeError("supervisor down"),
        RuntimeError("still down"),
        {"ok": True},
    ])
    runner = WorkerRunner(
        supervisor_url="http://test",
        worker_id="w-test",
        worker_name="worker",
        workspace=tmp_path,
        provider=_DummyProvider(),
        model="mock-model",
        poll_interval_s=0.01,
        supervisor_client=client,  # type: ignore[arg-type]
    )

    sleeps: list[float] = []

    async def _fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    async def _fake_poll_loop() -> None:
        runner._running = False

    async def _fake_heartbeat_loop() -> None:
        while runner._running:
            await _fake_sleep(0)

    monkeypatch.setattr("nanobot.worker.runner.asyncio.sleep", _fake_sleep)
    runner._poll_loop = _fake_poll_loop  # type: ignore[assignment]
    runner._heartbeat_loop = _fake_heartbeat_loop  # type: ignore[assignment]

    await runner.run()

    assert client.register_calls == 3
    assert sleeps == [0.01, 0.01]
    assert client.unregister_calls == 1
    assert client.close_calls == 1
"""Worker HTTP client — communicates with the Supervisor API."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from loguru import logger


class SupervisorClient:
    """HTTP client for worker → supervisor communication.

    All methods are async and use httpx for HTTP/1.1 persistent connections.
    Pass a pre-configured *http_client* (e.g. using ``ASGITransport``) to
    bypass real network traffic in tests.
    """

    def __init__(
        self,
        base_url: str,
        worker_id: str,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.worker_id = worker_id
        self._client = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, name: str, capabilities: list[str] | None = None) -> dict[str, Any]:
        resp = await self._client.post(
            "/api/v1/supervisor/workers/register",
            json={
                "worker_id": self.worker_id,
                "name": name,
                "capabilities": capabilities or [],
            },
        )
        resp.raise_for_status()
        return resp.json()

    async def unregister(self) -> None:
        try:
            resp = await self._client.delete(
                f"/api/v1/supervisor/workers/{self.worker_id}",
            )
            resp.raise_for_status()
        except Exception:
            logger.debug("Failed to cleanly unregister (supervisor may be down)")

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def heartbeat(
        self, current_task_id: str | None = None, status: str = "online"
    ) -> dict[str, Any]:
        resp = await self._client.post(
            f"/api/v1/supervisor/workers/{self.worker_id}/heartbeat",
            json={"current_task_id": current_task_id, "status": status},
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Task operations
    # ------------------------------------------------------------------

    async def claim_task(self, capabilities: list[str] | None = None) -> dict[str, Any] | None:
        """Try to claim a pending task. Returns task dict or None."""
        resp = await self._client.post(
            "/api/v1/supervisor/tasks/claim",
            json={"worker_id": self.worker_id, "capabilities": capabilities or []},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("task")

    async def report_progress(
        self,
        task_id: str,
        iteration: int = 0,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        resp = await self._client.post(
            f"/api/v1/supervisor/tasks/{task_id}/progress",
            json={
                "worker_id": self.worker_id,
                "iteration": iteration,
                "message": message,
                "data": data or {},
            },
        )
        resp.raise_for_status()

    async def report_result(
        self,
        task_id: str,
        status: str = "completed",
        result: str = "",
        error: str | None = None,
    ) -> None:
        resp = await self._client.post(
            f"/api/v1/supervisor/tasks/{task_id}/result",
            json={
                "worker_id": self.worker_id,
                "status": status,
                "result": result,
                "error": error,
            },
        )
        resp.raise_for_status()

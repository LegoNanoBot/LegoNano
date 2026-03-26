"""Supervisor API — worker endpoints (register, heartbeat, unregister)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(tags=["supervisor-workers"])


# ---------------------------------------------------------------------------
# Pydantic request / response schemas
# ---------------------------------------------------------------------------


class RegisterBody(BaseModel):
    worker_id: str
    name: str
    capabilities: list[str] = []
    base_url: str | None = None


class HeartbeatBody(BaseModel):
    current_task_id: str | None = None
    status: str = "online"


class WorkerOut(BaseModel):
    worker_id: str
    name: str
    status: str
    capabilities: list[str]
    registered_at: float
    last_heartbeat: float
    current_task_id: str | None
    base_url: str | None


def _worker_to_dict(w: Any) -> dict[str, Any]:
    return {
        "worker_id": w.worker_id,
        "name": w.name,
        "status": w.status.value if hasattr(w.status, "value") else w.status,
        "capabilities": w.capabilities,
        "registered_at": w.registered_at,
        "last_heartbeat": w.last_heartbeat,
        "current_task_id": w.current_task_id,
        "base_url": w.base_url,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/supervisor/workers/register")
async def register_worker(body: RegisterBody, request: Request) -> dict[str, Any]:
    from nanobot.supervisor.models import WorkerRegisterRequest

    registry = request.app.state.worker_registry
    req = WorkerRegisterRequest(
        worker_id=body.worker_id,
        name=body.name,
        capabilities=body.capabilities,
        base_url=body.base_url,
    )
    worker = await registry.register_worker(req)
    return {"ok": True, "worker": _worker_to_dict(worker)}


@router.post("/supervisor/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, body: HeartbeatBody, request: Request) -> dict[str, Any]:
    from nanobot.supervisor.models import HeartbeatRequest, WorkerStatus

    registry = request.app.state.worker_registry
    try:
        status = WorkerStatus(body.status)
    except ValueError:
        status = WorkerStatus.ONLINE
    req = HeartbeatRequest(
        worker_id=worker_id,
        current_task_id=body.current_task_id,
        status=status,
    )
    worker = await registry.heartbeat(req)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"ok": True, "worker": _worker_to_dict(worker)}


@router.delete("/supervisor/workers/{worker_id}")
async def unregister_worker(worker_id: str, request: Request) -> dict[str, Any]:
    registry = request.app.state.worker_registry
    removed = await registry.unregister_worker(worker_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"ok": True}


@router.get("/supervisor/workers")
async def list_workers(request: Request) -> dict[str, Any]:
    registry = request.app.state.worker_registry
    workers = await registry.list_workers()
    return {"workers": [_worker_to_dict(w) for w in workers]}


@router.get("/supervisor/workers/{worker_id}")
async def get_worker(worker_id: str, request: Request) -> dict[str, Any]:
    registry = request.app.state.worker_registry
    worker = await registry.get_worker(worker_id)
    if worker is None:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"worker": _worker_to_dict(worker)}

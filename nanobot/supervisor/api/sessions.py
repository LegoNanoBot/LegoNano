"""Supervisor API — distributed session endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["supervisor-sessions"])

_MAX_SESSION_PAYLOAD_BYTES = 256 * 1024


class SetSessionBody(BaseModel):
    value: dict[str, Any] = Field(default_factory=dict)


@router.get("/supervisor/sessions/{key}")
async def get_session(key: str, request: Request) -> dict[str, Any]:
    store = request.app.state.session_store
    value = await store.get_session(key)
    if value is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"key": key, "value": value}


@router.post("/supervisor/sessions/{key}")
async def set_session(key: str, body: SetSessionBody, request: Request) -> dict[str, Any]:
    store = request.app.state.session_store
    try:
        payload = json.dumps(body.value, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Session payload must be JSON serializable: {exc}") from exc

    if len(payload.encode("utf-8")) > _MAX_SESSION_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Session payload too large (limit {_MAX_SESSION_PAYLOAD_BYTES} bytes)",
        )

    await store.set_session(key, body.value)
    value = await store.get_session(key)
    return {"ok": True, "key": key, "value": value or {}}

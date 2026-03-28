"""Supervisor API — long-term memory endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(tags=["supervisor-memory"])


class PutLongTermBody(BaseModel):
    content: str = Field(default="", max_length=200_000)


class AppendHistoryBody(BaseModel):
    entry: str = Field(min_length=1, max_length=8_000)


@router.get("/supervisor/memory/context")
async def get_memory_context(request: Request) -> dict[str, Any]:
    memory_store = request.app.state.memory_store
    return {"context": memory_store.get_memory_context()}


@router.get("/supervisor/memory/long-term")
async def get_long_term_memory(request: Request) -> dict[str, Any]:
    memory_store = request.app.state.memory_store
    return {"content": memory_store.read_long_term()}


@router.put("/supervisor/memory/long-term")
async def put_long_term_memory(body: PutLongTermBody, request: Request) -> dict[str, Any]:
    memory_store = request.app.state.memory_store
    memory_store.write_long_term(body.content)
    return {"ok": True, "content": memory_store.read_long_term()}


@router.post("/supervisor/memory/history")
async def append_memory_history(body: AppendHistoryBody, request: Request) -> dict[str, Any]:
    memory_store = request.app.state.memory_store
    memory_store.append_history(body.entry)
    return {"ok": True}

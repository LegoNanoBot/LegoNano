"""API endpoints for the WebConsoleServer dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Request

from nanobot.WebConsoleServer.summary import build_system_summary

router = APIRouter(tags=["webconsole-api"])


@router.get("/webconsole/summary")
async def webconsole_summary(request: Request) -> dict:
    return await build_system_summary(request.app)
"""SSR page views for the phase-1 WebConsoleServer."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse

from nanobot.WebConsoleServer.summary import build_system_summary

router = APIRouter(tags=["webconsole-pages"])

_WEBCONSOLE_STATIC_DIR = Path(__file__).with_name("static")


def _get_asset_version() -> str:
    css_path = _WEBCONSOLE_STATIC_DIR / "webconsole.css"
    if not css_path.exists():
        return "dev"
    return str(int(css_path.stat().st_mtime_ns))


async def _build_page_context(request: Request) -> dict:
    context = await build_system_summary(request.app)
    context["asset_version"] = _get_asset_version()
    return context


async def _render_overview_fragment(request: Request) -> str:
    templates = request.app.state.webconsole_templates
    context = await _build_page_context(request)
    response = templates.TemplateResponse(request, "partials/overview.html", context=context)
    return response.body.decode("utf-8")


@router.get("/", response_class=HTMLResponse)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/console", status_code=302)


@router.get("/console", response_class=HTMLResponse)
async def console_index(request: Request):
    templates = request.app.state.webconsole_templates
    context = await _build_page_context(request)
    context["page"] = "console"
    return templates.TemplateResponse(request, "index.html", context=context)


@router.get("/console/partials/overview", response_class=HTMLResponse)
async def console_overview(request: Request):
    templates = request.app.state.webconsole_templates
    context = await _build_page_context(request)
    return templates.TemplateResponse(request, "partials/overview.html", context=context)


@router.get("/console/stream")
async def console_stream(
    request: Request,
    interval_s: float = Query(5.0, ge=0.1, le=60.0),
    max_updates: int | None = Query(None, ge=1, le=100),
):
    async def generate():
        emitted = 0
        while True:
            if await request.is_disconnected():
                break
            html = await _render_overview_fragment(request)
            yield {"event": "overview", "data": html}
            emitted += 1
            if max_updates is not None and emitted >= max_updates:
                break
            await asyncio.sleep(interval_s)

    return EventSourceResponse(generate())
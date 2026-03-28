"""Supervisor FastAPI application factory.

Composes the existing X-Ray app with supervisor-specific routers so that
a single uvicorn server exposes both monitoring and control-plane endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI
from loguru import logger

from nanobot.supervisor.event_sink import XRayCollectorEventSink
from nanobot.agent.memory import MemoryStore
from nanobot.supervisor.api import memory, plans, sessions, tasks, workers
from nanobot.supervisor.registry import WorkerRegistry
from nanobot.supervisor.session_store import DistributedSessionStore, InMemoryDistributedSessionStore

if TYPE_CHECKING:
    from nanobot.xray.collector import EventCollector
    from nanobot.xray.sse import SSEHub
    from nanobot.xray.store.base import BaseEventStore


def create_supervisor_app(
    *,
    worker_registry: WorkerRegistry | None = None,
    session_store: DistributedSessionStore | None = None,
    memory_store: MemoryStore | None = None,
    event_store: "BaseEventStore | None" = None,
    sse_hub: "SSEHub | None" = None,
    collector: "EventCollector | None" = None,
    config_refs: dict[str, Any] | None = None,
) -> FastAPI:
    """Create a FastAPI app that includes both X-Ray and supervisor routers.

    If the X-Ray dependencies are available and the stores are provided, the
    existing X-Ray routers are mounted as well, giving a unified API surface.
    """
    resolved_session_store = session_store or InMemoryDistributedSessionStore()

    @asynccontextmanager
    async def _lifespan(_app: FastAPI):
        await resolved_session_store.init()
        try:
            yield
        finally:
            try:
                await resolved_session_store.close()
            except Exception:
                logger.exception("Failed to close session store during supervisor shutdown")

    app = FastAPI(
        title="NanoBot Supervisor",
        description="Supervisor Gateway for distributed multi-bot collaboration",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        lifespan=_lifespan,
    )

    # Supervisor state
    registry = worker_registry or WorkerRegistry(
        event_sink=XRayCollectorEventSink(collector) if collector is not None else None,
    )
    app.state.worker_registry = registry
    app.state.session_store = resolved_session_store
    app.state.memory_store = memory_store or MemoryStore(Path.cwd())

    # Register supervisor API routers
    app.include_router(workers.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")
    app.include_router(plans.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(memory.router, prefix="/api/v1")

    # Mount X-Ray routers if stores are provided
    if event_store is not None and sse_hub is not None and collector is not None:
        from nanobot.xray.api import agents, config, events, tokens
        from nanobot.xray.pages import views as pages_views

        app.state.event_store = event_store
        app.state.sse_hub = sse_hub
        app.state.collector = collector
        app.state.config_refs = config_refs or {}

        app.include_router(agents.router, prefix="/api/v1")
        app.include_router(events.router, prefix="/api/v1")
        app.include_router(config.router, prefix="/api/v1")
        app.include_router(tokens.router, prefix="/api/v1")
        app.include_router(pages_views.router)

        # Static files and templates
        from fastapi.staticfiles import StaticFiles
        from fastapi.templating import Jinja2Templates

        static_dir = Path(__file__).parent.parent / "xray" / "static"
        static_dir.mkdir(exist_ok=True)
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

        templates_dir = Path(__file__).parent.parent / "xray" / "templates"
        templates_dir.mkdir(exist_ok=True)
        app.state.templates = Jinja2Templates(directory=str(templates_dir))

    return app

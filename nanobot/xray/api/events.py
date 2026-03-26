"""X-Ray event stream API endpoints."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, Request
from sse_starlette.sse import EventSourceResponse

from nanobot.xray.events import event_to_dict

router = APIRouter(tags=["events"])


@router.get("/events/stream")
async def event_stream(request: Request):
    """SSE real-time event stream."""
    sse_hub = request.app.state.sse_hub
    client_id, queue = sse_hub.subscribe()

    async def generate():
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.event_type,
                        "data": json.dumps(
                            event_to_dict(event), ensure_ascii=False, default=str
                        ),
                    }
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {"event": "ping", "data": ""}
        finally:
            sse_hub.unsubscribe(client_id)

    return EventSourceResponse(generate())


@router.get("/events/recent")
async def recent_events(
    request: Request,
    limit: int = Query(50, ge=1, le=500),
):
    """Get recent events from memory buffer."""
    collector = request.app.state.collector
    events = collector.get_recent(limit=limit)
    return {"events": [event_to_dict(e) for e in events], "count": len(events)}


@router.get("/status")
async def system_status(request: Request):
    """System status overview."""
    collector = request.app.state.collector
    sse_hub = request.app.state.sse_hub
    active_runs = collector.get_active_runs()
    return {
        "active_agents": len(active_runs),
        "sse_subscribers": sse_hub.subscriber_count,
        "buffer_size": len(collector._buffer),
    }

"""X-Ray token usage API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

router = APIRouter(tags=["tokens"])


@router.get("/tokens/summary")
async def token_summary(
    request: Request,
    run_id: str | None = Query(None, description="Filter by specific run"),
):
    """Token usage summary."""
    store = request.app.state.event_store
    usage = await store.get_token_usage(run_id=run_id)
    return usage

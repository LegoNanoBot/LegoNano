"""SSE (Server-Sent Events) broadcast hub for X-Ray."""

from __future__ import annotations

import asyncio
import uuid
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from nanobot.xray.events import XRayEvent


class SSEHub:
    """Manages SSE subscriptions and broadcasts events to connected clients."""

    def __init__(self) -> None:
        """Initialize the SSE hub with an empty subscriber registry."""
        self._subscribers: dict[str, asyncio.Queue[XRayEvent]] = {}

    def subscribe(self) -> tuple[str, asyncio.Queue[XRayEvent]]:
        """Create a new subscription.

        Returns:
            A tuple of (client_id, queue) for receiving events.
        """
        client_id = str(uuid.uuid4())
        queue: asyncio.Queue[XRayEvent] = asyncio.Queue(maxsize=100)
        self._subscribers[client_id] = queue
        logger.debug(f"SSE client subscribed: {client_id}")
        return client_id, queue

    def unsubscribe(self, client_id: str) -> None:
        """Remove a subscription.

        Args:
            client_id: The client identifier to unsubscribe.
        """
        if client_id in self._subscribers:
            del self._subscribers[client_id]
            logger.debug(f"SSE client unsubscribed: {client_id}")

    async def broadcast(self, event: XRayEvent) -> None:
        """Push an event to all subscribers.

        Non-blocking: uses put_nowait and skips full queues.

        Args:
            event: The event to broadcast.
        """
        for client_id, queue in list(self._subscribers.items()):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for client {client_id}, dropping event")

    @property
    def subscriber_count(self) -> int:
        """Return the number of active subscribers."""
        return len(self._subscribers)

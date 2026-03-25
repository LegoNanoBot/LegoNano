"""X-Ray observer for emitting monitoring events."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot.xray.events import XRayEvent, create_event

if TYPE_CHECKING:
    from nanobot.xray.collector import EventCollector


class XRayObserver:
    """Observer that emits X-Ray events to the collector."""

    def __init__(self, collector: EventCollector) -> None:
        """Initialize the observer with an event collector.

        Args:
            collector: The EventCollector to receive events.
        """
        self._collector = collector

    async def on_event(self, event: XRayEvent) -> None:
        """Handle an event by delegating to the collector.

        Exceptions are logged but not raised to avoid disrupting
        the main application flow.

        Args:
            event: The event to process.
        """
        try:
            await self._collector.collect(event)
        except Exception as e:
            logger.error(f"XRayObserver failed to handle event: {e}")

    async def emit(self, run_id: str, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Convenience method to create and emit an event.

        Args:
            run_id: The agent run identifier.
            event_type: One of EventType constants.
            data: Optional key-value payload.
        """
        event = create_event(run_id, event_type, data)
        await self.on_event(event)

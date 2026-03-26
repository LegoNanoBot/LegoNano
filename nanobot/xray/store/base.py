"""Abstract event store interface for X-Ray monitoring."""

from __future__ import annotations

from abc import ABC, abstractmethod

from nanobot.xray.events import XRayEvent


class BaseEventStore(ABC):
    """Storage contract for X-Ray monitoring events."""

    @abstractmethod
    async def init(self) -> None:
        """Initialize storage (create tables, etc.)."""

    @abstractmethod
    async def close(self) -> None:
        """Close connections and release resources."""

    @abstractmethod
    async def save_event(self, event: XRayEvent) -> None:
        """Save a single event to storage."""

    @abstractmethod
    async def save_events(self, events: list[XRayEvent]) -> None:
        """Save multiple events in batch."""

    @abstractmethod
    async def query_events(
        self,
        run_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """Query events with optional filters.

        Args:
            run_id: Filter by agent run ID.
            event_type: Filter by event type.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of event dictionaries.
        """

    @abstractmethod
    async def get_agent_runs(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Get list of agent runs.

        Args:
            status: Filter by run status ('active' or 'completed').
            limit: Maximum number of results.

        Returns:
            List of run info dictionaries.
        """

    @abstractmethod
    async def get_run_detail(self, run_id: str) -> dict | None:
        """Get detailed information for a single agent run.

        Args:
            run_id: The agent run identifier.

        Returns:
            Run detail dictionary or None if not found.
        """

    @abstractmethod
    async def get_token_usage(self, run_id: str | None = None) -> dict:
        """Get token usage statistics.

        Args:
            run_id: Optional run ID to filter by.

        Returns:
            Dictionary with token usage stats.
        """

    @abstractmethod
    async def cleanup(self, before_timestamp: float) -> int:
        """Delete events older than the specified timestamp.

        Args:
            before_timestamp: Unix timestamp threshold.

        Returns:
            Number of deleted rows.
        """

    async def store(self, event: XRayEvent) -> None:
        """Alias for save_event, used by EventCollector."""
        await self.save_event(event)

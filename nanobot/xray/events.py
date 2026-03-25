"""X-Ray event types and data models."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class EventType:
    """Constants for X-Ray event types."""

    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_END = "tool_call_end"
    SUBAGENT_SPAWN = "subagent_spawn"
    SUBAGENT_DONE = "subagent_done"
    MESSAGE_IN = "message_in"
    MESSAGE_OUT = "message_out"
    MEMORY_CONSOLIDATE = "memory_consolidate"
    ERROR = "error"


@dataclass
class XRayEvent:
    """Represents a single X-Ray monitoring event."""

    id: str
    timestamp: float
    run_id: str
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)


def create_event(run_id: str, event_type: str, data: dict[str, Any] | None = None) -> XRayEvent:
    """Factory function to create an XRayEvent with auto-generated id and timestamp.

    Args:
        run_id: The agent run identifier.
        event_type: One of EventType constants.
        data: Optional key-value payload.

    Returns:
        A new XRayEvent instance.
    """
    return XRayEvent(
        id=str(uuid.uuid4()),
        timestamp=time.time(),
        run_id=run_id,
        event_type=event_type,
        data=data or {},
    )


def event_to_dict(event: XRayEvent) -> dict[str, Any]:
    """Serialize an XRayEvent to a dictionary.

    Args:
        event: The event to serialize.

    Returns:
        Dictionary representation of the event.
    """
    return {
        "id": event.id,
        "timestamp": event.timestamp,
        "run_id": event.run_id,
        "event_type": event.event_type,
        "data": event.data,
    }

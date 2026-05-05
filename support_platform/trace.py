from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from support_platform.schemas import TraceEvent


class Tracer:
    """Collects structured trace events for a single support request."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    def add(self, event_type: str, reason: str, **metadata: Any) -> TraceEvent:
        event = TraceEvent(
            event_type=event_type,
            reason=reason,
            metadata=metadata,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._events.append(event)
        return event

    def get_events(self) -> list[TraceEvent]:
        return list(self._events)

    def summary(self) -> list[str]:
        return [f"[{e.event_type}] {e.reason}" for e in self._events]

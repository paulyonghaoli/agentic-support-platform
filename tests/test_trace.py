from __future__ import annotations

import pytest

from support_platform.trace import Tracer


def test_tracer_records_events():
    t = Tracer()
    t.add("REQUEST_RECEIVED", "User sent a message", user_id="u001")
    events = t.get_events()
    assert len(events) == 1
    assert events[0].event_type == "REQUEST_RECEIVED"
    assert events[0].reason == "User sent a message"
    assert events[0].metadata["user_id"] == "u001"


def test_tracer_records_multiple_events_in_order():
    t = Tracer()
    t.add("REQUEST_RECEIVED", "Start")
    t.add("INTENT_CLASSIFIED", "Classified as billing", intent="billing")
    t.add("RETRIEVAL_STARTED", "Fetching evidence")
    events = t.get_events()
    assert len(events) == 3
    assert events[0].event_type == "REQUEST_RECEIVED"
    assert events[1].event_type == "INTENT_CLASSIFIED"
    assert events[2].event_type == "RETRIEVAL_STARTED"


def test_tracer_events_have_timestamp():
    t = Tracer()
    t.add("EVIDENCE_FOUND", "Found 2 items")
    events = t.get_events()
    assert events[0].timestamp is not None
    assert "T" in events[0].timestamp  # ISO format


def test_tracer_metadata_stored():
    t = Tracer()
    t.add("EVALUATION_COMPLETED", "Scored response", score=0.85, risk="low")
    events = t.get_events()
    assert events[0].metadata["score"] == 0.85
    assert events[0].metadata["risk"] == "low"


def test_tracer_get_events_returns_copy():
    t = Tracer()
    t.add("REQUEST_RECEIVED", "Test")
    events1 = t.get_events()
    events1.append(None)  # Mutate the returned list
    events2 = t.get_events()
    assert len(events2) == 1  # Original unaffected


def test_tracer_summary_format():
    t = Tracer()
    t.add("REQUEST_RECEIVED", "User sent message")
    t.add("INTENT_CLASSIFIED", "Billing intent")
    summary = t.summary()
    assert len(summary) == 2
    assert "[REQUEST_RECEIVED]" in summary[0]
    assert "[INTENT_CLASSIFIED]" in summary[1]


def test_full_pipeline_trace_events():
    """Integration: orchestrator produces all expected trace event types."""
    from support_platform.orchestrator import Orchestrator
    from support_platform.schemas import SupportRequest

    orch = Orchestrator()
    response = orch.handle(SupportRequest(
        message="I'm traveling to Japan next week. What roaming option do I need?",
        user_id="demo_user_001",
    ))

    event_types = {e.event_type for e in response.trace}
    required_events = {
        "REQUEST_RECEIVED",
        "INTENT_CLASSIFIED",
        "RETRIEVAL_STARTED",
        "EVIDENCE_FOUND",
        "SPECIALIST_SELECTED",
        "RECOMMENDATION_BUILT",
        "EVALUATION_COMPLETED",
        "RESPONSE_FINALIZED",
    }
    missing = required_events - event_types
    assert not missing, f"Missing trace events: {missing}"

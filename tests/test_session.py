from __future__ import annotations

import time

import pytest

from support_platform.session.store import SessionStore
from support_platform.session.followup import (
    apply_intent_carryover,
    extract_slot_value,
    is_followup_response,
)
from support_platform.schemas import Intent


# ---------------------------------------------------------------------------
# SessionStore tests
# ---------------------------------------------------------------------------

def test_session_store_returns_none_for_unknown_user():
    store = SessionStore()
    assert store.get("nobody") is None


def test_session_store_saves_and_retrieves():
    store = SessionStore()
    store.update("user1", last_intent="billing", last_missing_slot="device_type")
    session = store.get("user1")
    assert session is not None
    assert session["last_intent"] == "billing"
    assert session["last_missing_slot"] == "device_type"


def test_session_store_merges_slots():
    store = SessionStore()
    store.update("user1", slots={"device_type": "iPhone"})
    store.update("user1", slots={"network_type": "LTE"})
    session = store.get("user1")
    assert session["slots"]["device_type"] == "iPhone"
    assert session["slots"]["network_type"] == "LTE"


def test_session_store_ttl_expires():
    store = SessionStore(ttl_seconds=1)
    store.update("user1", last_intent="billing")
    time.sleep(1.1)
    assert store.get("user1") is None


def test_session_store_appends_messages():
    store = SessionStore()
    store.update("user1", add_message={"role": "user", "content": "Hello"})
    store.update("user1", add_message={"role": "assistant", "content": "Hi"})
    session = store.get("user1")
    assert len(session["messages"]) == 2
    assert session["messages"][0]["role"] == "user"


def test_session_store_trims_message_history():
    store = SessionStore()
    for i in range(15):
        store.update("user1", add_message={"role": "user", "content": f"msg {i}"})
    session = store.get("user1")
    assert len(session["messages"]) <= 10  # _MAX_HISTORY


def test_session_store_clear():
    store = SessionStore()
    store.update("user1", last_intent="billing")
    store.clear("user1")
    assert store.get("user1") is None


def test_session_store_increment_turn():
    store = SessionStore()
    store.increment_turn("user1")
    store.increment_turn("user1")
    session = store.get("user1")
    assert session["turn_count"] == 2


def test_session_store_active_count():
    store = SessionStore()
    store.update("a", last_intent="billing")
    store.update("b", last_intent="roaming")
    assert store.active_count() == 2


# ---------------------------------------------------------------------------
# Follow-up detection tests
# ---------------------------------------------------------------------------

def test_is_followup_returns_false_without_session():
    assert is_followup_response("iPhone", session=None, confidence=0.0) is False


def test_is_followup_returns_false_without_missing_slot():
    session = {"last_intent": "connectivity_troubleshooting", "last_missing_slot": None}
    assert is_followup_response("iPhone", session=session, confidence=0.0) is False


def test_is_followup_short_message_with_missing_slot():
    session = {"last_missing_slot": "device_type", "last_intent": "connectivity_troubleshooting"}
    assert is_followup_response("It's an iPhone", session=session, confidence=0.0) is True


def test_is_followup_low_confidence_triggers_carryover():
    session = {"last_missing_slot": "device_type", "last_intent": "connectivity_troubleshooting"}
    assert is_followup_response(
        "My phone does not connect and I tried everything already",
        session=session,
        confidence=0.1,
    ) is True


def test_is_followup_long_message_high_confidence_not_followup():
    session = {"last_missing_slot": "device_type", "last_intent": "connectivity_troubleshooting"}
    assert is_followup_response(
        "I want to know about roaming options for my trip to Japan next week",
        session=session,
        confidence=0.9,
    ) is False


# ---------------------------------------------------------------------------
# Slot extraction tests
# ---------------------------------------------------------------------------

def test_extract_device_type_iphone():
    assert extract_slot_value("device_type", "It's an iPhone 14") == "iPhone"


def test_extract_device_type_android():
    assert extract_slot_value("device_type", "Samsung Galaxy") == "Android (Samsung)"


def test_extract_device_type_pixel():
    assert extract_slot_value("device_type", "I use a Pixel 7") == "Android (Pixel)"


def test_extract_network_type_lte():
    assert extract_slot_value("network_type", "It shows LTE") == "LTE"


def test_extract_network_type_no_service():
    assert extract_slot_value("network_type", "It says No Service") == "No Service"


def test_extract_yes_no_yes():
    assert extract_slot_value("recent_plan_change", "Yes I changed it recently") == "yes"


def test_extract_yes_no_no():
    assert extract_slot_value("recent_plan_change", "No I haven't changed anything") == "no"


def test_extract_watch_model_apple_watch():
    val = extract_slot_value("watch_model", "Apple Watch Series 8")
    assert val == "Apple Watch Series 8"


def test_extract_watch_model_galaxy():
    val = extract_slot_value("watch_model", "Samsung Galaxy Watch 5")
    assert val is not None
    assert "Galaxy Watch" in val or "Samsung" in val


def test_extract_frequency_constant():
    assert extract_slot_value("frequency", "It's always like this") == "constant"


def test_extract_frequency_intermittent():
    assert extract_slot_value("frequency", "It comes and goes") == "intermittent"


def test_extract_location_home():
    assert extract_slot_value("location_type", "It's at my home") == "home"


def test_extract_country_japan():
    val = extract_slot_value("current_country", "I'm going to Japan")
    assert val is not None and "Japan" in val


def test_extract_short_message_verbatim_fallback():
    # Very short message with unrecognised slot — return verbatim
    val = extract_slot_value("when_started", "Yesterday")
    assert val == "Yesterday"


# ---------------------------------------------------------------------------
# Intent carry-over tests
# ---------------------------------------------------------------------------

def test_intent_carryover_low_confidence_uses_session():
    session = {"last_intent": "roaming"}
    result = apply_intent_carryover(Intent.UNSUPPORTED, confidence=0.1, session=session)
    assert result == Intent.ROAMING


def test_intent_carryover_high_confidence_keeps_new_intent():
    session = {"last_intent": "roaming"}
    result = apply_intent_carryover(Intent.BILLING, confidence=0.8, session=session)
    assert result == Intent.BILLING


def test_intent_carryover_no_session_returns_intent():
    result = apply_intent_carryover(Intent.BILLING, confidence=0.1, session=None)
    assert result == Intent.BILLING


def test_intent_carryover_invalid_stored_intent_falls_back():
    session = {"last_intent": "not_a_real_intent"}
    result = apply_intent_carryover(Intent.UNSUPPORTED, confidence=0.1, session=session)
    assert result == Intent.UNSUPPORTED


# ---------------------------------------------------------------------------
# Integration: multi-turn slot filling through orchestrator
# ---------------------------------------------------------------------------

def test_multiturn_slot_filling():
    """
    Turn 1: vague connectivity complaint → ask about device type
    Turn 2: short answer ('iPhone') → slot filled, steps returned
    """
    from support_platform.orchestrator import Orchestrator
    from support_platform.schemas import SupportRequest

    orch = Orchestrator()
    user_id = "test_multiturn_user_999"

    # Turn 1
    r1 = orch.handle(SupportRequest(message="My data is not working.", user_id=user_id))
    assert r1.intent == "connectivity_troubleshooting"
    assert "?" in r1.answer  # asking a follow-up question
    missing_slots_1 = r1.session_state_summary.missing_slots if r1.session_state_summary else []

    # Turn 2: answer the follow-up
    r2 = orch.handle(SupportRequest(message="It's an iPhone.", user_id=user_id))
    # Should have filled device_type slot
    known_in_r2 = (r2.session_state_summary.known_slots or {}) if r2.session_state_summary else {}
    assert "device_type" in known_in_r2
    assert known_in_r2["device_type"] == "iPhone"


def test_multiturn_session_state_summary_present():
    from support_platform.orchestrator import Orchestrator
    from support_platform.schemas import SupportRequest

    orch = Orchestrator()
    r = orch.handle(SupportRequest(message="My data stopped working.", user_id="test_summary_user_888"))
    assert r.session_state_summary is not None
    assert r.session_state_summary.intent is not None
    assert r.session_state_summary.turn_count >= 1


def test_multiturn_trace_contains_session_events():
    from support_platform.orchestrator import Orchestrator
    from support_platform.schemas import SupportRequest

    orch = Orchestrator()
    r = orch.handle(SupportRequest(message="I'm traveling to Japan.", user_id="test_trace_session_777"))
    event_types = {e.event_type for e in r.trace}
    assert "SESSION_LOADED" in event_types
    assert "INTENT_CLASSIFIED" in event_types

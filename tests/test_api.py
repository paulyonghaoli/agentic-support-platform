from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from support_platform.api import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_support_endpoint_returns_200():
    response = client.post("/support", json={
        "message": "I'm traveling to Japan next week. What roaming option do I need?",
        "user_id": "demo_user_001",
        "debug": True,
    })
    assert response.status_code == 200


def test_support_response_has_required_fields():
    response = client.post("/support", json={
        "message": "Why is my bill higher this month?",
        "user_id": "demo_user_002",
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "intent" in data
    assert "agent_path" in data
    assert "evidence_ids" in data
    assert "escalation" in data
    assert "evaluation" in data
    assert "trace" in data


def test_support_response_intent_is_valid():
    response = client.post("/support", json={
        "message": "My data stopped working.",
        "user_id": "demo_user_003",
    })
    data = response.json()
    valid_intents = {
        "billing", "plan_recommendation", "roaming",
        "connectivity_troubleshooting", "device_iot_activation", "unsupported"
    }
    assert data["intent"] in valid_intents


def test_support_response_evaluation_shape():
    response = client.post("/support", json={
        "message": "My family uses 80GB per month. Should we change plans?",
        "user_id": "demo_user_002",
    })
    data = response.json()
    ev = data["evaluation"]
    assert 0.0 <= ev["groundedness"] <= 1.0
    assert 0.0 <= ev["completeness"] <= 1.0
    assert 0.0 <= ev["user_success_likelihood"] <= 1.0
    assert ev["fallback_risk"] in ("low", "medium", "high")
    assert ev["latency_category"] in ("fast", "normal", "slow")


def test_support_response_agent_path_is_list():
    response = client.post("/support", json={
        "message": "I'm traveling to Japan.",
        "user_id": "demo_user_001",
    })
    data = response.json()
    assert isinstance(data["agent_path"], list)
    assert len(data["agent_path"]) >= 3
    assert "intent_router" in data["agent_path"]
    assert "evaluation_agent" in data["agent_path"]


def test_support_response_trace_is_list():
    response = client.post("/support", json={
        "message": "Which plan is best for heavy data use?",
        "user_id": "demo_user_003",
    })
    data = response.json()
    assert isinstance(data["trace"], list)
    assert len(data["trace"]) > 0
    first_event = data["trace"][0]
    assert "event_type" in first_event
    assert "reason" in first_event


def test_escalation_field_is_boolean():
    response = client.post("/support", json={
        "message": "I want a refund for this charge.",
        "user_id": "demo_user_002",
    })
    data = response.json()
    assert isinstance(data["escalation"], bool)


def test_roaming_response_includes_roaming_evidence():
    response = client.post("/support", json={
        "message": "I'm traveling to Japan next week. What roaming option do I need?",
        "user_id": "demo_user_001",
    })
    data = response.json()
    assert data["intent"] == "roaming"
    assert any("roaming" in eid for eid in data["evidence_ids"])


def test_proactive_signals_for_high_usage_account():
    response = client.post("/support", json={
        "message": "My bill seems higher.",
        "user_id": "demo_user_001",  # 96% data usage + upcoming Japan trip
    })
    data = response.json()
    # Should have proactive signals for this account
    assert data.get("proactive_signals") is not None
    assert len(data["proactive_signals"]) > 0


def test_voice_demo_returns_html():
    response = client.get("/voice-demo")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"voice" in response.content.lower()

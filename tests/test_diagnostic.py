from __future__ import annotations

import pytest

from support_platform.agents.diagnostic_agent import DiagnosticAgent
from support_platform.schemas import Intent


@pytest.fixture
def agent() -> DiagnosticAgent:
    return DiagnosticAgent(client=None)


def test_missing_slot_for_generic_connectivity(agent):
    result = agent.diagnose(
        "My internet is not working.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence=[],
        account=None,
    )
    assert result.missing_slots, "Should detect missing slots for vague connectivity complaint"
    assert result.follow_up_question is not None


def test_data_after_plan_change_returns_steps(agent, demo_account_003):
    result = agent.diagnose(
        "My mobile data stopped working after I changed plans.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence=[],
        account=demo_account_003,
    )
    # demo_user_003 has recent_plan_change=True
    assert result.diagnostic_steps is not None
    assert len(result.diagnostic_steps) >= 2
    assert result.follow_up_question is None


def test_repeated_failures_trigger_escalation(agent, demo_account_004):
    result = agent.diagnose(
        "I keep losing signal indoors.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence=[],
        account=demo_account_004,
    )
    # demo_user_004 has 4 connectivity tickets in 90 days
    assert result.should_escalate is True
    assert result.escalation_reason is not None


def test_smartwatch_without_model_asks_follow_up(agent):
    result = agent.diagnose(
        "My smartwatch is not connecting.",
        Intent.DEVICE_IOT_ACTIVATION,
        evidence=[],
        account=None,
    )
    assert result.follow_up_question is not None
    assert "watch" in result.follow_up_question.lower() or "model" in result.follow_up_question.lower()


def test_apple_watch_with_model_returns_steps(agent):
    result = agent.diagnose(
        "My Apple Watch Series 8 is not connecting to cellular.",
        Intent.DEVICE_IOT_ACTIVATION,
        evidence=[],
        account=None,
    )
    assert result.diagnostic_steps is not None
    assert len(result.diagnostic_steps) >= 2


def test_diagnostic_confidence_between_0_and_1(agent):
    result = agent.diagnose(
        "No data connection.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence=[],
        account=None,
    )
    assert 0.0 <= result.confidence <= 1.0


def test_indoor_signal_asks_follow_up(agent):
    result = agent.diagnose(
        "I keep losing signal inside my house.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence=[],
        account=None,
    )
    assert result.follow_up_question is not None

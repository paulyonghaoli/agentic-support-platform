from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from support_platform.agents.escalation_agent import _wants_human, check_escalation
from support_platform.schemas import Intent


def test_unsupported_intent_always_escalates():
    decision = check_escalation("What is the capital of France?", Intent.UNSUPPORTED, account=None)
    assert decision.should_escalate is True
    assert decision.trigger_rule == "unsupported_intent"


def test_user_requests_human_agent_escalates():
    decision = check_escalation(
        "I want to speak to a human agent.",
        Intent.BILLING,
        account=None,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "user_requested_human"


def test_billing_dispute_escalates():
    decision = check_escalation(
        "I want a refund for this unauthorized charge.",
        Intent.BILLING,
        account=None,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "billing_action_required"


def test_billing_question_no_action_does_not_escalate():
    decision = check_escalation(
        "Why is my bill higher this month?",
        Intent.BILLING,
        account=None,
    )
    assert decision.should_escalate is False


def test_repeated_connectivity_failures_escalate(demo_account_004):
    # demo_user_004 has 4 connectivity tickets in 90 days
    decision = check_escalation(
        "I keep losing signal indoors.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        account=demo_account_004,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "repeated_connectivity_failure"


def test_normal_connectivity_no_escalation(demo_account_001):
    decision = check_escalation(
        "My data stopped working.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        account=demo_account_001,
    )
    assert decision.should_escalate is False


def test_diagnostic_escalation_bubbles_up():
    from support_platform.schemas import DiagnosticResult
    diag = DiagnosticResult(
        missing_slots=[],
        follow_up_question=None,
        diagnostic_steps=None,
        confidence=0.9,
        should_escalate=True,
        escalation_reason="Device activation blocked.",
    )
    decision = check_escalation(
        "My watch won't activate.",
        Intent.DEVICE_IOT_ACTIVATION,
        account=None,
        diagnostic_result=diag,
    )
    assert decision.should_escalate is True
    assert "activation" in (decision.reason or "").lower()


def test_low_confidence_diagnostic_escalates():
    from support_platform.schemas import DiagnosticResult
    diag = DiagnosticResult(
        missing_slots=["device_type"],
        follow_up_question="What device?",
        diagnostic_steps=None,
        confidence=0.2,
        should_escalate=False,
    )
    decision = check_escalation(
        "Something is wrong.",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        account=None,
        diagnostic_result=diag,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "low_confidence"


def test_device_activation_blocked_after_multiple_attempts():
    decision = check_escalation(
        "I've tried twice and my watch still not working after all the steps.",
        Intent.DEVICE_IOT_ACTIVATION,
        account=None,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "device_activation_blocked"


def test_escalation_decision_has_reason_when_escalating():
    decision = check_escalation("Delete my account.", Intent.UNSUPPORTED, account=None)
    assert decision.should_escalate is True
    assert decision.reason is not None


def test_manager_request_escalates():
    decision = check_escalation(
        "I need to speak to your manager right now.",
        Intent.BILLING,
        account=None,
    )
    assert decision.should_escalate is True
    assert decision.trigger_rule == "user_requested_human"


def test_repeated_connectivity_only_fires_for_connectivity_intent(demo_account_004):
    # Rule 4 should NOT fire for billing requests even if account has many tickets
    decision = check_escalation(
        "Why is my bill higher this month?",
        Intent.BILLING,
        account=demo_account_004,
    )
    assert decision.trigger_rule != "repeated_connectivity_failure"


def test_wants_human_no_signal_skips_llm():
    mock_client = MagicMock()
    result = _wants_human("Why is my bill so high?", mock_client)
    assert result is False
    mock_client.chat.completions.create.assert_not_called()


def test_wants_human_with_mock_client_returns_true():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps({"wants_human": True})
    mock_client.chat.completions.create.return_value = mock_response

    result = _wants_human("I'd like to speak to someone who can actually help", mock_client)
    assert result is True
    mock_client.chat.completions.create.assert_called_once()


def test_wants_human_llm_failure_falls_back_to_phrases():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    result = _wants_human("I want to speak to a human agent", mock_client)
    assert result is True  # phrase list catches "human agent"

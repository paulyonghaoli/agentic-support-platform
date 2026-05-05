from __future__ import annotations

import pytest

from support_platform.agents.evaluation_agent import evaluate
from support_platform.schemas import EscalationDecision, Intent


def _make_escalation(escalate: bool = False, reason: str = None, rule: str = None) -> EscalationDecision:
    return EscalationDecision(should_escalate=escalate, reason=reason, trigger_rule=rule)


def test_evaluation_returns_correct_shape():
    result = evaluate(
        message="Why is my bill higher?",
        answer="Your bill may be higher due to overage fees.",
        intent=Intent.BILLING,
        evidence_ids=["billing_high_001"],
        escalation=_make_escalation(),
    )
    assert 0.0 <= result.groundedness <= 1.0
    assert 0.0 <= result.completeness <= 1.0
    assert 0.0 <= result.user_success_likelihood <= 1.0
    assert 0.0 <= result.safety_correctness <= 1.0
    assert result.fallback_risk in ("low", "medium", "high")
    assert result.latency_category in ("fast", "normal", "slow")


def test_evaluation_with_evidence_has_higher_groundedness():
    with_evidence = evaluate(
        message="Roaming question",
        answer="The Japan/Korea Pack costs $25/month and provides 5 GB data.",
        intent=Intent.ROAMING,
        evidence_ids=["roaming_japan_001"],
        escalation=_make_escalation(),
    )
    without_evidence = evaluate(
        message="Roaming question",
        answer="Here is some information.",
        intent=Intent.ROAMING,
        evidence_ids=[],
        escalation=_make_escalation(),
    )
    assert with_evidence.groundedness >= without_evidence.groundedness


def test_correct_escalation_has_high_safety():
    result = evaluate(
        message="I want a refund.",
        answer="This has been escalated to a human agent.",
        intent=Intent.BILLING,
        evidence_ids=[],
        escalation=_make_escalation(
            escalate=True,
            reason="Billing action required.",
            rule="billing_action_required",
        ),
    )
    assert result.safety_correctness >= 0.9


def test_unsupported_without_escalation_has_low_safety():
    result = evaluate(
        message="Hack into this account.",
        answer="I can help with that.",
        intent=Intent.UNSUPPORTED,
        evidence_ids=[],
        escalation=_make_escalation(escalate=False),
    )
    assert result.safety_correctness < 0.5


def test_latency_fast_under_1_5_seconds():
    result = evaluate(
        message="billing question",
        answer="Your bill is processed monthly.",
        intent=Intent.BILLING,
        evidence_ids=[],
        escalation=_make_escalation(),
        elapsed_seconds=0.5,
    )
    assert result.latency_category == "fast"


def test_latency_slow_over_5_seconds():
    result = evaluate(
        message="billing question",
        answer="Your bill is processed monthly.",
        intent=Intent.BILLING,
        evidence_ids=[],
        escalation=_make_escalation(),
        elapsed_seconds=6.0,
    )
    assert result.latency_category == "slow"


def test_average_score_is_mean_of_four_dimensions():
    result = evaluate(
        message="test",
        answer="test answer with plan data and $25 per month for gb unlimited",
        intent=Intent.PLAN_RECOMMENDATION,
        evidence_ids=["plan_001"],
        escalation=_make_escalation(),
    )
    expected = (
        result.groundedness
        + result.completeness
        + result.user_success_likelihood
        + result.safety_correctness
    ) / 4
    assert abs(result.average_score() - expected) < 0.001


def test_low_scores_produce_high_fallback_risk():
    result = evaluate(
        message="unclear question",
        answer="ok",  # Very short answer
        intent=Intent.CONNECTIVITY_TROUBLESHOOTING,
        evidence_ids=[],
        escalation=_make_escalation(),
    )
    assert result.fallback_risk in ("medium", "high")

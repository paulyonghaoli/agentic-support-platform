from __future__ import annotations

import time

from support_platform.schemas import EscalationDecision, EvaluationResult, Intent


def evaluate(
    message: str,
    answer: str,
    intent: Intent,
    evidence_ids: list[str],
    escalation: EscalationDecision,
    diagnostic_result=None,
    recommendation_result=None,
    elapsed_seconds: float = 0.0,
) -> EvaluationResult:
    """
    Rule-based evaluation of the final response.
    Returns a structured EvaluationResult with scores 0.0–1.0.
    """
    groundedness = _score_groundedness(answer, evidence_ids, intent, recommendation_result)
    completeness = _score_completeness(answer, intent, escalation, diagnostic_result)
    user_success = _score_user_success(intent, escalation, diagnostic_result, recommendation_result)
    safety = _score_safety(intent, escalation)
    fallback_risk = _assess_fallback_risk(groundedness, completeness, user_success)
    latency_cat = _categorize_latency(elapsed_seconds)

    return EvaluationResult(
        groundedness=groundedness,
        completeness=completeness,
        user_success_likelihood=user_success,
        safety_correctness=safety,
        fallback_risk=fallback_risk,
        latency_category=latency_cat,
    )


def _score_groundedness(
    answer: str,
    evidence_ids: list[str],
    intent: Intent,
    recommendation_result=None,
) -> float:
    if not evidence_ids and intent not in (Intent.PLAN_RECOMMENDATION,):
        return 0.3

    answer_lower = answer.lower()
    plan_terms = ["plan", "$", "gb", "unlimited", "add-on", "roaming", "per month"]
    evidence_terms = ["guide", "policy", "per your", "based on", "steps", "according"]

    matched = sum(1 for t in plan_terms + evidence_terms if t in answer_lower)
    base = min(0.4 + matched * 0.06, 0.95)

    if evidence_ids:
        base = min(base + 0.1, 0.95)

    if recommendation_result and getattr(recommendation_result, "evidence_ids", []):
        base = min(base + 0.05, 0.95)

    return round(base, 2)


def _score_completeness(
    answer: str,
    intent: Intent,
    escalation: EscalationDecision,
    diagnostic_result=None,
) -> float:
    if escalation.should_escalate:
        # Escalation response needs: explanation + case reference + next steps
        has_explanation = len(answer) > 80
        has_next_step = any(w in answer.lower() for w in ["agent", "support", "contact", "business day", "escalat"])
        return round(0.5 + (0.25 if has_explanation else 0) + (0.25 if has_next_step else 0), 2)

    if diagnostic_result is not None:
        missing = getattr(diagnostic_result, "missing_slots", [])
        steps = getattr(diagnostic_result, "diagnostic_steps", None)
        follow_up = getattr(diagnostic_result, "follow_up_question", None)

        if missing and follow_up:
            # Asking a follow-up — completeness is moderate (appropriately incomplete)
            return 0.65
        if steps:
            has_steps = len(steps) >= 2
            has_context = len(answer) > 100
            return round(0.6 + (0.2 if has_steps else 0) + (0.15 if has_context else 0), 2)

    # General completeness heuristic based on answer length and structure
    word_count = len(answer.split())
    if word_count < 20:
        return 0.3
    if word_count < 50:
        return 0.55
    if word_count < 120:
        return 0.75
    return 0.85


def _score_user_success(
    intent: Intent,
    escalation: EscalationDecision,
    diagnostic_result=None,
    recommendation_result=None,
) -> float:
    if escalation.should_escalate:
        # Escalation is correct behavior — but user success depends on human follow-up
        return 0.6

    if intent in (Intent.PLAN_RECOMMENDATION, Intent.ROAMING):
        if recommendation_result:
            has_option = bool(getattr(recommendation_result, "recommended_option", ""))
            has_rationale = len(getattr(recommendation_result, "rationale", "")) > 30
            return round(0.55 + (0.2 if has_option else 0) + (0.2 if has_rationale else 0), 2)
        return 0.5

    if diagnostic_result is not None:
        confidence = getattr(diagnostic_result, "confidence", 0.5)
        steps = getattr(diagnostic_result, "diagnostic_steps", None)
        follow_up = getattr(diagnostic_result, "follow_up_question", None)

        if follow_up:
            return 0.55  # Need more info — uncertain outcome

        if steps:
            return round(min(0.5 + confidence * 0.5, 0.9), 2)

    return 0.5


def _score_safety(intent: Intent, escalation: EscalationDecision) -> float:
    if intent == Intent.UNSUPPORTED and not escalation.should_escalate:
        return 0.3  # Should have escalated
    if escalation.should_escalate and escalation.trigger_rule in (
        "billing_action_required",
        "repeated_connectivity_failure",
        "live_roaming_failure",
        "device_activation_blocked",
        "user_requested_human",
        "unsupported_intent",
    ):
        return 1.0  # Correct escalation
    return 0.9  # Non-escalation responses are generally safe


def _assess_fallback_risk(
    groundedness: float,
    completeness: float,
    user_success: float,
) -> str:
    avg = (groundedness + completeness + user_success) / 3
    if avg >= 0.75:
        return "low"
    if avg >= 0.5:
        return "medium"
    return "high"


def _categorize_latency(elapsed_seconds: float) -> str:
    if elapsed_seconds < 1.5:
        return "fast"
    if elapsed_seconds < 5.0:
        return "normal"
    return "slow"

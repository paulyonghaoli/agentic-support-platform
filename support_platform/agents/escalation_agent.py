from __future__ import annotations

from support_platform.schemas import EscalationDecision, Intent


def check_escalation(
    message: str,
    intent: Intent,
    account: dict | None,
    diagnostic_result=None,
    recommendation_result=None,
    confidence: float = 1.0,
) -> EscalationDecision:
    """
    Rule-based escalation check. Returns an EscalationDecision.
    Deterministic by design — no LLM involved.
    """
    msg = message.lower()

    # 1. Unsupported intent
    if intent == Intent.UNSUPPORTED:
        return EscalationDecision(
            should_escalate=True,
            reason="Request is outside supported AI support scope.",
            trigger_rule="unsupported_intent",
        )

    # 2. User explicitly requests human agent
    if any(phrase in msg for phrase in ["human agent", "speak to someone", "talk to a person", "real person", "human support"]):
        return EscalationDecision(
            should_escalate=True,
            reason="User explicitly requested human support.",
            trigger_rule="user_requested_human",
        )

    # 3. Account-specific billing action required
    if intent == Intent.BILLING:
        billing_action_phrases = [
            "refund", "credit", "dispute", "waive", "remove charge",
            "unauthorized", "cancel", "billing date", "wrong charge",
        ]
        if any(p in msg for p in billing_action_phrases):
            return EscalationDecision(
                should_escalate=True,
                reason="Billing action requires a human agent (refund, dispute, or unauthorized charge).",
                trigger_rule="billing_action_required",
            )

    # 4. Repeated connectivity failures
    if account and account.get("connectivity_tickets_last_90d", 0) >= 3:
        return EscalationDecision(
            should_escalate=True,
            reason=f"Repeated connectivity issues: {account['connectivity_tickets_last_90d']} tickets in 90 days. Network team review required.",
            trigger_rule="repeated_connectivity_failure",
        )

    # 5. Diagnostic escalation bubble-up
    if diagnostic_result is not None and getattr(diagnostic_result, "should_escalate", False):
        reason = getattr(diagnostic_result, "escalation_reason", None) or "Diagnostic agent determined escalation is needed."
        return EscalationDecision(
            should_escalate=True,
            reason=reason,
            trigger_rule="diagnostic_escalation",
        )

    # 6. Low confidence after diagnosis attempt
    if diagnostic_result is not None:
        diag_confidence = getattr(diagnostic_result, "confidence", 1.0)
        if diag_confidence < 0.4:
            return EscalationDecision(
                should_escalate=True,
                reason="Insufficient information to resolve issue with confidence. Handing off to human support.",
                trigger_rule="low_confidence",
            )

    # 7. Live roaming failure (user is currently abroad and can't connect)
    if intent == Intent.CONNECTIVITY_TROUBLESHOOTING or intent == Intent.ROAMING:
        abroad_phrases = ["currently abroad", "i'm in", "right now in", "can't connect here", "already traveling"]
        roaming_fail_phrases = ["roaming not working", "can't use data abroad", "no signal abroad"]
        if any(p in msg for p in abroad_phrases + roaming_fail_phrases):
            return EscalationDecision(
                should_escalate=True,
                reason="Live roaming or connectivity failure while abroad requires real-time network support.",
                trigger_rule="live_roaming_failure",
            )

    # 8. Device activation blocked after multiple attempts
    if intent == Intent.DEVICE_IOT_ACTIVATION:
        blocked_phrases = ["still not working", "tried everything", "failed again", "doesn't work after", "second time"]
        if any(p in msg for p in blocked_phrases):
            return EscalationDecision(
                should_escalate=True,
                reason="Device activation appears blocked after multiple attempts. Manual provisioning required.",
                trigger_rule="device_activation_blocked",
            )

    return EscalationDecision(should_escalate=False)

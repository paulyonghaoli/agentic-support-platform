from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from support_platform.schemas import EscalationDecision, Intent

# Broad signal words used to skip the LLM call when there is clearly no human-request intent.
# If none of these appear, _wants_human returns False immediately with no LLM call.
_HUMAN_SIGNAL_WORDS = frozenset([
    "manager", "supervisor", "human", "person", "someone", "agent",
    "speak", "talk", "transfer", "escalate", "connect", "put me",
])

_BILLING_ACTION_PHRASES = [
    "refund", "credit", "dispute", "waive", "remove charge",
    "unauthorized", "cancel", "billing date", "wrong charge",
]

# Fallback phrase list used when no LLM client is available
_HUMAN_REQUEST_PHRASES = [
    "human agent", "speak to someone", "talk to a person", "real person", "human support",
    "speak to your manager", "speak to a manager", "talk to your manager", "talk to a manager",
    "speak to your supervisor", "talk to your supervisor", "get your manager",
    "manager", "supervisor", "escalate this", "escalate to", "want a human",
    "connect me to", "transfer me", "put me through",
]


def _wants_human(message: str, client: Optional[OpenAI]) -> bool:
    """
    Returns True if the message indicates the user wants a human agent.

    Fast path: returns False immediately if no rough signal words are present,
    avoiding any LLM call on the majority of requests.
    When a signal exists: uses LLM for flexible intent understanding if available,
    then falls back to exact phrase matching.
    """
    msg = message.lower()
    if not any(s in msg for s in _HUMAN_SIGNAL_WORDS):
        return False

    if client is not None:
        try:
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a classifier. Respond only with JSON.\n"
                            'Return {"wants_human": true} if the user wants to speak with a human agent, '
                            "manager, or supervisor, or is asking to escalate to a person.\n"
                            'Return {"wants_human": false} for everything else.'
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0,
                max_tokens=20,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            return bool(data.get("wants_human", False))
        except Exception:
            pass  # fall through to phrase matching

    return any(phrase in msg for phrase in _HUMAN_REQUEST_PHRASES)


def check_escalation(
    message: str,
    intent: Intent,
    account: dict | None,
    diagnostic_result=None,
    recommendation_result=None,
    confidence: float = 1.0,
    client: Optional[OpenAI] = None,
) -> EscalationDecision:
    """
    Rule-based escalation check. Returns an EscalationDecision.
    Rule 2 uses an LLM signal when a client is available; all other rules are deterministic.
    """
    msg = message.lower()

    # 1. Unsupported intent
    if intent == Intent.UNSUPPORTED:
        return EscalationDecision(
            should_escalate=True,
            reason="Request is outside supported AI support scope.",
            trigger_rule="unsupported_intent",
        )

    # 2. User explicitly requests human agent (LLM signal; phrase-list fallback)
    if _wants_human(message, client):
        return EscalationDecision(
            should_escalate=True,
            reason="User requested to speak with a human agent.",
            trigger_rule="user_requested_human",
        )

    # 3. Account-specific billing action required
    if intent == Intent.BILLING:
        if any(p in msg for p in _BILLING_ACTION_PHRASES):
            return EscalationDecision(
                should_escalate=True,
                reason="Billing action requires a human agent (refund, dispute, or unauthorized charge).",
                trigger_rule="billing_action_required",
            )

    # 4. Repeated connectivity failures (only relevant for connectivity/device intents)
    if (
        intent in (Intent.CONNECTIVITY_TROUBLESHOOTING, Intent.DEVICE_IOT_ACTIVATION)
        and account
        and account.get("connectivity_tickets_last_90d", 0) >= 3
    ):
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
    if intent in (Intent.CONNECTIVITY_TROUBLESHOOTING, Intent.ROAMING):
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

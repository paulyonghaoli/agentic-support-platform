from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from support_platform.schemas import DiagnosticResult, Evidence, Intent

# ---------------------------------------------------------------------------
# Slot definitions per intent
# ---------------------------------------------------------------------------

_REQUIRED_SLOTS: dict[str, dict] = {
    "connectivity": {
        "device_type": "What type of device are you using (e.g., iPhone, Android phone, other)?",
        "network_type": "Are you seeing 'No Service', 'LTE', '5G', or something else in your status bar?",
        "when_started": "Did this start immediately after a specific change (plan change, SIM swap, update)?",
    },
    "indoor_signal": {
        "location_type": "Is this happening at home, in your office, or in a specific building?",
        "frequency": "Is this constant or intermittent?",
    },
    "watch_activation": {
        "watch_model": "What model smartwatch are you trying to activate (e.g., Apple Watch Series 8, Samsung Galaxy Watch)?",
        "paired_phone": "What phone is paired with the watch?",
        "wearable_addon": "Do you have the wearable add-on active on your account ($10/month)?",
    },
    "roaming": {
        "current_country": "Which country are you in (or traveling to)?",
        "roaming_addon": "Do you have a roaming add-on active on your account?",
    },
}

_SYSTEM_PROMPT = """You are a telecom support diagnostic agent.
Given a user message, retrieved troubleshooting guides, and user account context,
produce a structured diagnostic response.

Your response must be a JSON object with these fields:
{
  "missing_slots": ["list of missing info needed"],
  "follow_up_question": "single focused question if info is missing, else null",
  "diagnostic_steps": ["step 1", "step 2", ...] or null if follow-up needed,
  "confidence": 0.0-1.0,
  "should_escalate": true/false,
  "escalation_reason": "reason if escalating, else null"
}

Rules:
- Ask at most ONE follow-up question. Pick the most critical missing piece.
- If you have enough info, provide 2-4 actionable steps.
- Escalate if: problem recurs 3+ times, device activation fails after 2+ attempts, live roaming failure.
- Base steps ONLY on the retrieved guides; do not invent steps not in the guides.
- Keep steps concise and non-technical where possible."""


class DiagnosticAgent:
    def __init__(self, client: Optional[OpenAI] = None) -> None:
        self._client = client
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def diagnose(
        self,
        message: str,
        intent: Intent,
        evidence: list[Evidence],
        account: dict | None,
    ) -> DiagnosticResult:
        # Check for mandatory escalation from account history
        if account:
            if account.get("connectivity_tickets_last_90d", 0) >= 3:
                return DiagnosticResult(
                    missing_slots=[],
                    follow_up_question=None,
                    diagnostic_steps=None,
                    confidence=0.9,
                    should_escalate=True,
                    escalation_reason="Repeated connectivity issues (3+ tickets in 90 days) require network team review.",
                )

        if self._client is None:
            return self._deterministic_diagnose(message, intent, evidence, account)

        return self._llm_diagnose(message, intent, evidence, account)

    def _llm_diagnose(
        self,
        message: str,
        intent: Intent,
        evidence: list[Evidence],
        account: dict | None,
    ) -> DiagnosticResult:
        evidence_text = "\n\n".join(
            f"[{e.id}]\n{e.content[:600]}" for e in evidence
        )
        account_context = _format_account(account)

        user_content = f"""User message: {message}

Account context:
{account_context}

Retrieved troubleshooting guides:
{evidence_text or "No guides retrieved."}"""

        try:
            import json

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            return DiagnosticResult(
                missing_slots=data.get("missing_slots", []),
                follow_up_question=data.get("follow_up_question"),
                diagnostic_steps=data.get("diagnostic_steps"),
                confidence=float(data.get("confidence", 0.5)),
                should_escalate=bool(data.get("should_escalate", False)),
                escalation_reason=data.get("escalation_reason"),
            )
        except Exception:
            return self._deterministic_diagnose(message, intent, evidence, account)

    def _deterministic_diagnose(
        self,
        message: str,
        intent: Intent,
        evidence: list[Evidence],
        account: dict | None,
    ) -> DiagnosticResult:
        """Rule-based fallback when LLM is unavailable."""
        msg = message.lower()

        # Smartwatch / IoT
        if intent == Intent.DEVICE_IOT_ACTIVATION or any(
            w in msg for w in ["watch", "smartwatch", "wearable"]
        ):
            missing = []
            if not any(w in msg for w in ["apple watch", "galaxy watch", "samsung watch"]):
                missing.append("watch_model")
            if missing:
                return DiagnosticResult(
                    missing_slots=missing,
                    follow_up_question=_REQUIRED_SLOTS["watch_activation"]["watch_model"],
                    diagnostic_steps=None,
                    confidence=0.4,
                    should_escalate=False,
                )
            return DiagnosticResult(
                missing_slots=[],
                follow_up_question=None,
                diagnostic_steps=[
                    "Confirm the wearable add-on ($10/month) is active on your account.",
                    "Open the paired phone app (Watch app or Galaxy Wearable) and navigate to Cellular > Remove Plan > Re-add Plan.",
                    "Restart both the watch and the phone after re-provisioning.",
                    "If activation fails again, contact support — a manual provisioning fix is needed.",
                ],
                confidence=0.7,
                should_escalate=False,
            )

        # Data not working after plan change
        if account and account.get("recent_plan_change"):
            return DiagnosticResult(
                missing_slots=[],
                follow_up_question=None,
                diagnostic_steps=[
                    "Toggle airplane mode off and on to force network re-registration.",
                    "Restart your device.",
                    "Check APN settings: it should be set to 'synthtel.net'.",
                    "Wait up to 2 hours after plan activation — provisioning may still be in progress.",
                    "If the issue persists after 2 hours, contact support.",
                ],
                confidence=0.75,
                should_escalate=False,
            )

        # Indoor signal
        if "indoor" in msg or "inside" in msg or "home" in msg or "office" in msg:
            return DiagnosticResult(
                missing_slots=["frequency"],
                follow_up_question="Is the signal loss constant or does it come and go?",
                diagnostic_steps=None,
                confidence=0.5,
                should_escalate=False,
            )

        # Generic connectivity
        if intent == Intent.CONNECTIVITY_TROUBLESHOOTING:
            return DiagnosticResult(
                missing_slots=["device_type", "network_type"],
                follow_up_question="What device are you using, and what does your signal bar show (No Service, LTE, 5G)?",
                diagnostic_steps=None,
                confidence=0.4,
                should_escalate=False,
            )

        # Fallback
        return DiagnosticResult(
            missing_slots=["device_type"],
            follow_up_question="Could you describe your device and the exact issue you're experiencing?",
            diagnostic_steps=None,
            confidence=0.3,
            should_escalate=False,
        )


def _format_account(account: dict | None) -> str:
    if not account:
        return "No account data available."
    return (
        f"Plan: {account.get('current_plan', 'unknown')}\n"
        f"Devices: {', '.join(account.get('devices', []))}\n"
        f"Recent plan change: {account.get('recent_plan_change', False)}\n"
        f"Connectivity tickets (90d): {account.get('connectivity_tickets_last_90d', 0)}\n"
        f"Open tickets: {account.get('open_tickets', 0)}"
    )

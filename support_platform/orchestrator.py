from __future__ import annotations

import os
import time
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

from support_platform.agents.diagnostic_agent import DiagnosticAgent
from support_platform.agents.escalation_agent import check_escalation
from support_platform.agents.evaluation_agent import evaluate
from support_platform.agents.intent_router import IntentRouter
from support_platform.agents.recommendation_agent import RecommendationAgent
from support_platform.agents.retrieval_agent import RetrievalAgent
from support_platform.data.loaders import get_data_store
from support_platform.proactive.signals import detect_signals
from support_platform.schemas import (
    EscalationDecision,
    Intent,
    SessionStateSummary,
    SupportRequest,
    SupportResponse,
)
from support_platform.session.followup import (
    apply_intent_carryover,
    extract_slot_value,
    is_followup_response,
)
from support_platform.session.store import get_session_store
from support_platform.trace import Tracer

load_dotenv()


def _build_escalation_answer(escalation: EscalationDecision, user_id: str) -> str:
    case_ref = f"CASE-{user_id.upper()[-8:]}-{int(time.time()) % 100000}"
    return (
        f"This issue has been escalated to our support team.\n\n"
        f"**Reason:** {escalation.reason}\n\n"
        f"Your case reference is **{case_ref}**. "
        "A support agent will reach out within 1 business day. "
        "You can also contact us directly via the SynthTel support portal."
    )


def _build_diagnostic_answer(result) -> str:
    if result.follow_up_question:
        return (
            "To help diagnose your issue, I need a bit more information:\n\n"
            f"**{result.follow_up_question}**\n\n"
            "Once I have this, I can walk you through the right troubleshooting steps."
        )
    if result.diagnostic_steps:
        steps_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(result.diagnostic_steps))
        return (
            "Here are the recommended steps to resolve your issue:\n\n"
            f"{steps_text}\n\n"
            "If the issue persists after trying these steps, please contact support for further assistance."
        )
    return "I wasn't able to identify a specific resolution. A support agent can help you further."


def _build_recommendation_answer(result, intent: Intent) -> str:
    topic = "plan" if intent == Intent.PLAN_RECOMMENDATION else "roaming option"
    lines = [f"Based on your usage and needs, here is the recommended {topic}:\n"]
    lines.append(f"**Recommended:** {result.recommended_option}")
    if result.rationale:
        lines.append(f"\n{result.rationale}")
    if result.alternatives:
        alts = ", ".join(result.alternatives)
        lines.append(f"\n**Alternatives to consider:** {alts}")
    if result.limitations:
        lims = "; ".join(l for l in result.limitations if l.strip())
        lines.append(f"\n**Important notes:** {lims}")
    return "\n".join(lines)


def _build_billing_answer(evidence, account: dict | None) -> str:
    if not evidence:
        return (
            "For billing questions, please review your itemized bill in MyAccount > Billing > Current Bill. "
            "If you'd like to dispute a charge, use MyAccount > Billing > Dispute a Charge. "
            "For charges over $50 or unauthorized charges, a human agent is required."
        )
    top = evidence[0]
    lines = [l.strip() for l in top.content.split("\n") if l.strip() and not l.startswith("#")]
    excerpt = " ".join(lines[:4])
    return (
        f"{excerpt}\n\n"
        "To review your full bill, visit MyAccount > Billing > Current Bill. "
        "For disputes, use MyAccount > Billing > Dispute a Charge."
    )


class Orchestrator:
    """
    Central coordinator for the support pipeline.
    Flow: session → intent → retrieval → specialist → escalation → evaluation → response → session
    """

    def __init__(self) -> None:
        self._store = get_data_store()
        self._sessions = get_session_store()
        client = self._build_openai_client()

        self._intent_router = IntentRouter(
            client=client,
            use_llm_fallback=os.getenv("USE_LLM_FALLBACK", "true").lower() == "true",
        )
        self._retrieval = RetrievalAgent(self._store)
        self._diagnostic = DiagnosticAgent(client=client)
        self._recommendation = RecommendationAgent(client=client)

    @staticmethod
    def _build_openai_client() -> Optional[OpenAI]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        return OpenAI(api_key=api_key)

    def handle(self, request: SupportRequest) -> SupportResponse:
        tracer = Tracer()
        start = time.time()
        agent_path: list[str] = []

        # ── Step 0: Load session ─────────────────────────────────────────
        session = self._sessions.get(request.user_id)
        tracer.add(
            "SESSION_LOADED",
            f"Session {'found' if session else 'not found'} for {request.user_id}",
            user_id=request.user_id,
            turn_count=(session or {}).get("turn_count", 0),
            known_slots=list((session or {}).get("slots", {}).keys()),
        )

        # ── Step 1: Receive request ──────────────────────────────────────
        tracer.add(
            "REQUEST_RECEIVED",
            f"User {request.user_id} sent a support request",
            user_id=request.user_id,
            message_length=len(request.message),
        )

        # ── Step 2: Load account context ─────────────────────────────────
        account = self._retrieval.retrieve_account(request.user_id)

        # ── Step 3: Classify intent ──────────────────────────────────────
        agent_path.append("intent_router")
        intent, confidence = self._intent_router.route(request.message)

        # ── Step 3a: Follow-up + slot filling ────────────────────────────
        known_slots: dict[str, str] = dict((session or {}).get("slots", {}))
        followup_detected = False

        if is_followup_response(request.message, session, confidence):
            followup_detected = True
            tracer.add(
                "FOLLOWUP_DETECTED",
                "Message appears to be a follow-up answer to a previous question",
                last_missing_slot=(session or {}).get("last_missing_slot"),
                session_intent=(session or {}).get("last_intent"),
            )
            last_missing = (session or {}).get("last_missing_slot")
            if last_missing:
                slot_value = extract_slot_value(last_missing, request.message)
                if slot_value:
                    known_slots[last_missing] = slot_value
                    tracer.add(
                        "SLOT_FILLED",
                        f"Slot '{last_missing}' filled with value '{slot_value}'",
                        slot=last_missing,
                        value=slot_value,
                    )

        # ── Step 3b: Intent carry-over ────────────────────────────────────
        intent = apply_intent_carryover(intent, confidence, session)
        tracer.add(
            "INTENT_CLASSIFIED",
            f"Intent '{intent.value}' with confidence {confidence:.2f}",
            intent=intent.value,
            confidence=confidence,
            followup=followup_detected,
            carried_over=followup_detected and bool(session and session.get("last_intent")),
        )

        if known_slots:
            tracer.add(
                "CONTEXT_APPLIED",
                f"Applying {len(known_slots)} known slot(s) from session",
                slots=known_slots,
            )

        # ── Step 4: Retrieve evidence ────────────────────────────────────
        agent_path.append("retrieval_agent")
        tracer.add("RETRIEVAL_STARTED", f"Searching evidence for intent '{intent.value}'", intent=intent.value)
        evidence = self._retrieval.retrieve(intent, request.message)
        tracer.add(
            "EVIDENCE_FOUND",
            f"Retrieved {len(evidence)} evidence item(s)",
            evidence_ids=[e.id for e in evidence],
            count=len(evidence),
        )

        # ── Step 5: Proactive signals ────────────────────────────────────
        proactive_signals: list[str] = []
        if account:
            proactive_signals = detect_signals(account)

        # ── Step 6: Route to specialist ──────────────────────────────────
        diagnostic_result = None
        recommendation_result = None
        answer = ""

        if intent in (Intent.CONNECTIVITY_TROUBLESHOOTING, Intent.DEVICE_IOT_ACTIVATION):
            agent_path.append("diagnostic_agent")
            tracer.add("SPECIALIST_SELECTED", "Routing to diagnostic agent", agent="diagnostic_agent")
            diagnostic_result = self._diagnostic.diagnose(
                request.message, intent, evidence, account, known_slots=known_slots
            )
            if diagnostic_result.missing_slots:
                tracer.add(
                    "MISSING_SLOT_DETECTED",
                    f"Missing info: {', '.join(diagnostic_result.missing_slots)}",
                    slots=diagnostic_result.missing_slots,
                )
            else:
                tracer.add(
                    "DIAGNOSTIC_STEPS_BUILT",
                    f"Built {len(diagnostic_result.diagnostic_steps or [])} diagnostic steps",
                    steps_count=len(diagnostic_result.diagnostic_steps or []),
                )
            answer = _build_diagnostic_answer(diagnostic_result)

        elif intent in (Intent.PLAN_RECOMMENDATION, Intent.ROAMING):
            agent_path.append("recommendation_agent")
            tracer.add("SPECIALIST_SELECTED", "Routing to recommendation agent", agent="recommendation_agent")
            plans = self._retrieval.retrieve_plans()
            recommendation_result = self._recommendation.recommend(
                request.message, intent, evidence, account, plans
            )
            tracer.add(
                "RECOMMENDATION_BUILT",
                f"Recommended: {recommendation_result.recommended_option}",
                option=recommendation_result.recommended_option,
            )
            answer = _build_recommendation_answer(recommendation_result, intent)

        elif intent == Intent.BILLING:
            agent_path.append("billing_handler")
            tracer.add("SPECIALIST_SELECTED", "Handling billing query", agent="billing_handler")
            answer = _build_billing_answer(evidence, account)

        else:
            tracer.add("SPECIALIST_SELECTED", "Intent is unsupported", agent="escalation_agent")

        # ── Step 7: Escalation check ─────────────────────────────────────
        escalation = check_escalation(
            message=request.message,
            intent=intent,
            account=account,
            diagnostic_result=diagnostic_result,
            recommendation_result=recommendation_result,
            confidence=confidence,
        )

        if escalation.should_escalate:
            agent_path.append("escalation_agent")
            tracer.add(
                "ESCALATION_TRIGGERED",
                escalation.reason or "Escalation required",
                trigger_rule=escalation.trigger_rule,
            )
            answer = _build_escalation_answer(escalation, request.user_id)

        # ── Step 8: Evaluate ─────────────────────────────────────────────
        agent_path.append("evaluation_agent")
        elapsed = time.time() - start
        eval_result = evaluate(
            message=request.message,
            answer=answer,
            intent=intent,
            evidence_ids=[e.id for e in evidence],
            escalation=escalation,
            diagnostic_result=diagnostic_result,
            recommendation_result=recommendation_result,
            elapsed_seconds=elapsed,
        )
        tracer.add(
            "EVALUATION_COMPLETED",
            f"Avg score {eval_result.average_score():.2f}, fallback_risk={eval_result.fallback_risk}",
            groundedness=eval_result.groundedness,
            completeness=eval_result.completeness,
            user_success=eval_result.user_success_likelihood,
            fallback_risk=eval_result.fallback_risk,
        )

        tracer.add("RESPONSE_FINALIZED", f"Response ready for user {request.user_id}", agent_path=agent_path)

        # ── Step 9: Save session ─────────────────────────────────────────
        self._sessions.update(request.user_id, last_intent=intent.value)
        if known_slots:
            self._sessions.update(request.user_id, slots=known_slots)
        self._sessions.update(request.user_id, last_response=answer)
        self._sessions.update(
            request.user_id,
            add_message={"role": "user", "content": request.message},
        )
        self._sessions.update(
            request.user_id,
            add_message={"role": "assistant", "content": answer[:200]},
        )

        # Store last missing slot so next turn can fill it
        next_missing = (
            diagnostic_result.missing_slots[0]
            if diagnostic_result and diagnostic_result.missing_slots
            else None
        )
        self._sessions.update(request.user_id, last_missing_slot=next_missing)
        self._sessions.increment_turn(request.user_id)

        # Build session summary for response
        updated_session = self._sessions.get(request.user_id) or {}
        session_summary = SessionStateSummary(
            intent=intent.value,
            known_slots=updated_session.get("slots", {}),
            missing_slots=diagnostic_result.missing_slots if diagnostic_result else [],
            turn_count=updated_session.get("turn_count", 1),
        )

        return SupportResponse(
            answer=answer,
            intent=intent.value,
            agent_path=agent_path,
            evidence_ids=[e.id for e in evidence],
            escalation=escalation.should_escalate,
            escalation_reason=escalation.reason if escalation.should_escalate else None,
            evaluation=eval_result,
            trace=tracer.get_events(),
            proactive_signals=proactive_signals if proactive_signals else None,
            session_state_summary=session_summary,
        )


# Module-level singleton
_orchestrator: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

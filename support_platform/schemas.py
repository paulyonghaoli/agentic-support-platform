from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Intent(str, Enum):
    BILLING = "billing"
    PLAN_RECOMMENDATION = "plan_recommendation"
    ROAMING = "roaming"
    CONNECTIVITY_TROUBLESHOOTING = "connectivity_troubleshooting"
    DEVICE_IOT_ACTIVATION = "device_iot_activation"
    UNSUPPORTED = "unsupported"


class Evidence(BaseModel):
    id: str
    source: str
    content: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class TraceEvent(BaseModel):
    event_type: str
    reason: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class EvaluationResult(BaseModel):
    groundedness: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    user_success_likelihood: float = Field(ge=0.0, le=1.0)
    safety_correctness: float = Field(ge=0.0, le=1.0)
    fallback_risk: str  # "low", "medium", "high"
    latency_category: str  # "fast", "normal", "slow"

    def average_score(self) -> float:
        return (
            self.groundedness
            + self.completeness
            + self.user_success_likelihood
            + self.safety_correctness
        ) / 4


class SupportRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    debug: bool = False


class SessionStateSummary(BaseModel):
    intent: Optional[str] = None
    known_slots: dict[str, str] = Field(default_factory=dict)
    missing_slots: list[str] = Field(default_factory=list)
    turn_count: int = 0


class SupportResponse(BaseModel):
    answer: str
    intent: str
    agent_path: list[str]
    evidence_ids: list[str]
    escalation: bool
    escalation_reason: Optional[str] = None
    evaluation: EvaluationResult
    trace: list[TraceEvent]
    proactive_signals: Optional[list[str]] = None
    session_state_summary: Optional[SessionStateSummary] = None


class DiagnosticResult(BaseModel):
    missing_slots: list[str]
    follow_up_question: Optional[str]
    diagnostic_steps: Optional[list[str]]
    confidence: float
    should_escalate: bool
    escalation_reason: Optional[str] = None


class RecommendationResult(BaseModel):
    recommended_option: str
    alternatives: list[str]
    rationale: str
    limitations: list[str]
    evidence_ids: list[str]


class EscalationDecision(BaseModel):
    should_escalate: bool
    reason: Optional[str] = None
    trigger_rule: Optional[str] = None

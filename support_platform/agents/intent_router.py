from __future__ import annotations

import json
import os
from typing import Optional

from openai import OpenAI

from support_platform.schemas import Intent

# ---------------------------------------------------------------------------
# Keyword patterns for deterministic first-pass classification
# ---------------------------------------------------------------------------

_KEYWORD_MAP: dict[Intent, list[str]] = {
    Intent.BILLING: [
        "bill", "billing", "charge", "charged", "payment", "invoice",
        "fee", "cost", "overcharge", "refund", "credit", "dispute",
        "higher bill", "extra charge", "third-party", "premium sms",
    ],
    Intent.PLAN_RECOMMENDATION: [
        "which plan", "best plan", "change plan", "change plans", "switch plan",
        "upgrade my plan", "should we change plans", "recommend a plan", "family plan",
        "should i switch", "should i upgrade", "data usage", "gb per month", "downgrade",
        "my current plan", "data plan", "current plan",
    ],
    Intent.ROAMING: [
        "roaming", "travel", "traveling", "travelling", "international",
        "abroad", "japan", "europe", "korea", "visiting", "trip",
        "fly", "flight", "country", "overseas",
    ],
    Intent.CONNECTIVITY_TROUBLESHOOTING: [
        "not working", "stopped working", "no signal", "lost signal", "losing signal",
        "disconnected", "slow internet", "data stopped", "no data",
        "connection problem", "signal dropped", "indoor signal", "weak signal",
        "no service", "data not working",
    ],
    Intent.DEVICE_IOT_ACTIVATION: [
        "smartwatch", "watch", "tablet", "iot", "device", "activate",
        "activation", "esim", "e-sim", "not connecting", "wearable",
        "apple watch", "galaxy watch", "ipad",
    ],
}

_SYSTEM_PROMPT = """You are an intent classifier for a telecom support system.
Classify the user message into exactly one of these intents:
- billing
- plan_recommendation
- roaming
- connectivity_troubleshooting
- device_iot_activation
- unsupported

Respond with a JSON object: {"intent": "<intent>", "confidence": <0.0-1.0>}
Only respond with JSON. No explanation."""


def _keyword_score(message: str) -> dict[Intent, float]:
    msg = message.lower()
    scores: dict[Intent, float] = {}
    for intent, keywords in _KEYWORD_MAP.items():
        hits = sum(1 for kw in keywords if kw in msg)
        scores[intent] = hits / len(keywords)
    return scores


class IntentRouter:
    def __init__(self, client: Optional[OpenAI] = None, use_llm_fallback: bool = True) -> None:
        self._client = client
        self._use_llm = use_llm_fallback and client is not None
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def route(self, message: str) -> tuple[Intent, float]:
        """
        Returns (intent, confidence).
        Uses keyword matching first; falls back to LLM only when ambiguous.
        """
        scores = _keyword_score(message)
        best_intent = max(scores, key=scores.__getitem__)
        best_score = scores[best_intent]

        # Scale: 1 keyword hit ≈ 0.4 confidence, 2+ ≈ ≥0.7
        confidence = min(best_score * 7, 1.0)

        # Zero keyword hits = clearly unsupported; LLM should not override this
        if confidence == 0.0:
            return Intent.UNSUPPORTED, 0.0

        if confidence >= 0.3 or not self._use_llm:
            return best_intent, confidence

        # Ambiguous — ask the LLM
        return self._llm_classify(message)

    def _llm_classify(self, message: str) -> tuple[Intent, float]:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0,
                max_tokens=60,
            )
            raw = response.choices[0].message.content.strip()
            data = json.loads(raw)
            intent_str = data.get("intent", "unsupported")
            confidence = float(data.get("confidence", 0.5))
            try:
                intent = Intent(intent_str)
            except ValueError:
                intent = Intent.UNSUPPORTED
            return intent, confidence
        except Exception:
            return Intent.UNSUPPORTED, 0.0

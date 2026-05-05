from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from support_platform.schemas import Evidence, Intent, RecommendationResult

_PLAN_SYSTEM_PROMPT = """You are a telecom plan recommendation agent.
Given a user's message, their account context, and the available plan catalog,
recommend the best plan option. Be specific, grounded in the data, and honest about tradeoffs.

Your response must be a JSON object:
{
  "recommended_option": "plan_id or add-on name",
  "alternatives": ["other_plan_id", ...],
  "rationale": "2-3 sentence explanation grounded in the user's usage and plan data",
  "limitations": ["limitation 1", "limitation 2"]
}

Rules:
- Never recommend more than one primary option. List alternatives separately.
- Always mention the price.
- Note any limitations (e.g., no roaming, shared data).
- Do not over-sell — if the user's current plan is adequate, say so.
- Base recommendations ONLY on the provided plan data."""

_ROAMING_SYSTEM_PROMPT = """You are a telecom roaming recommendation agent.
Given a user's travel context and the available roaming add-ons,
recommend the best roaming option.

Your response must be a JSON object:
{
  "recommended_option": "add-on name with evidence ID",
  "alternatives": ["other option", ...],
  "rationale": "2-3 sentence explanation",
  "limitations": ["limitation 1", ...]
}

Rules:
- Check if the destination country is supported.
- Recommend the most cost-effective option for the trip duration.
- Always mention activation requirements (must activate before departure).
- Include the evidence ID (e.g., roaming_japan_001) in the recommended_option."""


class RecommendationAgent:
    def __init__(self, client: Optional[OpenAI] = None) -> None:
        self._client = client
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def recommend(
        self,
        message: str,
        intent: Intent,
        evidence: list[Evidence],
        account: dict | None,
        plans: list[dict],
    ) -> RecommendationResult:
        if intent == Intent.ROAMING:
            return self._recommend_roaming(message, evidence, account)
        return self._recommend_plan(message, evidence, account, plans)

    def _recommend_plan(
        self,
        message: str,
        evidence: list[Evidence],
        account: dict | None,
        plans: list[dict],
    ) -> RecommendationResult:
        if self._client is None:
            return self._deterministic_plan_recommendation(message, account, plans)

        plan_text = _format_plans(plans)
        account_context = _format_account(account)

        user_content = f"""User message: {message}

Account context:
{account_context}

Available plans:
{plan_text}"""

        try:
            import json

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _PLAN_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content.strip())
            return RecommendationResult(
                recommended_option=data.get("recommended_option", "unknown"),
                alternatives=data.get("alternatives", []),
                rationale=data.get("rationale", ""),
                limitations=data.get("limitations", []),
                evidence_ids=[e.id for e in evidence],
            )
        except Exception:
            return self._deterministic_plan_recommendation(message, account, plans)

    def _recommend_roaming(
        self,
        message: str,
        evidence: list[Evidence],
        account: dict | None,
    ) -> RecommendationResult:
        if self._client is None:
            return self._deterministic_roaming_recommendation(message, evidence, account)

        evidence_text = "\n\n".join(f"[{e.id}]\n{e.content[:600]}" for e in evidence)
        account_context = _format_account(account)

        user_content = f"""User message: {message}

Account context:
{account_context}

Retrieved roaming policies:
{evidence_text or "No policies retrieved."}"""

        try:
            import json

            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _ROAMING_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content.strip())
            return RecommendationResult(
                recommended_option=data.get("recommended_option", "unknown"),
                alternatives=data.get("alternatives", []),
                rationale=data.get("rationale", ""),
                limitations=data.get("limitations", []),
                evidence_ids=[e.id for e in evidence],
            )
        except Exception:
            return self._deterministic_roaming_recommendation(message, evidence, account)

    # ------------------------------------------------------------------
    # Deterministic fallbacks
    # ------------------------------------------------------------------

    def _deterministic_plan_recommendation(
        self, message: str, account: dict | None, plans: list[dict]
    ) -> RecommendationResult:
        msg = message.lower()
        current_plan_id = account.get("current_plan") if account else None
        current_plan = next((p for p in plans if p["plan_id"] == current_plan_id), None)

        # Family use case
        if "family" in msg or "80gb" in msg or "80 gb" in msg:
            target = next((p for p in plans if p["plan_id"] == "family_unlimited"), plans[-1])
            alts = [p["plan_id"] for p in plans if p["plan_id"] == "family_60gb"]
            return RecommendationResult(
                recommended_option=target["plan_id"],
                alternatives=alts,
                rationale=(
                    f"Based on ~80 GB/month family usage, the {target['name']} "
                    f"(${target['monthly_price_usd']}/mo) avoids overage fees. "
                    f"The Family 60GB plan would incur ~$300/mo in overage charges at that usage."
                ),
                limitations=target.get("limitations", "").split(". "),
                evidence_ids=[],
            )

        # Heavy individual user
        if "unlimited" in msg or (account and account.get("monthly_data_used_gb", 0) > 15):
            target = next((p for p in plans if p["plan_id"] == "unlimited_plus"), plans[0])
            return RecommendationResult(
                recommended_option=target["plan_id"],
                alternatives=["standard_20gb"],
                rationale=(
                    f"The {target['name']} (${target['monthly_price_usd']}/mo) "
                    "provides truly unlimited data with no overage risk. "
                    "Data is deprioritized (not cut off) after 50 GB during congestion."
                ),
                limitations=target.get("limitations", "").split(". "),
                evidence_ids=[],
            )

        # Default: recommend standard
        target = next((p for p in plans if p["plan_id"] == "standard_20gb"), plans[0])
        return RecommendationResult(
            recommended_option=target["plan_id"],
            alternatives=["basic_5gb", "unlimited_plus"],
            rationale=(
                f"The {target['name']} (${target['monthly_price_usd']}/mo) "
                "offers a good balance of data, hotspot, and 5G for most users."
            ),
            limitations=target.get("limitations", "").split(". "),
            evidence_ids=[],
        )

    def _deterministic_roaming_recommendation(
        self, message: str, evidence: list[Evidence], account: dict | None
    ) -> RecommendationResult:
        msg = message.lower()

        if "japan" in msg or "korea" in msg or "south korea" in msg:
            return RecommendationResult(
                recommended_option="Japan/Korea Pack — $25/month [roaming_japan_001]",
                alternatives=["International Roaming 10GB — $60/month [roaming_monthly_10gb_001]"],
                rationale=(
                    "The Japan/Korea Pack ($25/mo) provides 5 GB of data in Japan and South Korea "
                    "with unlimited calls and SMS — the most cost-effective option for a Japan trip. "
                    "Activate at least 24 hours before departure."
                ),
                limitations=["Does not cover other countries", "Must activate before departure"],
                evidence_ids=["roaming_japan_001"],
            )

        if any(c in msg for c in ["europe", "uk", "france", "germany", "spain", "italy"]):
            return RecommendationResult(
                recommended_option="Europe Pack — $35/month [roaming_europe_001]",
                alternatives=["International Roaming 10GB — $60/month [roaming_monthly_10gb_001]"],
                rationale=(
                    "The Europe Pack ($35/mo) covers all supported European countries with 8 GB data. "
                    "Activate before departure to ensure provisioning."
                ),
                limitations=["Does not cover countries outside Europe pack list", "Must activate before departure"],
                evidence_ids=["roaming_europe_001"],
            )

        return RecommendationResult(
            recommended_option="International Roaming 10GB — $60/month [roaming_monthly_10gb_001]",
            alternatives=["Day Pass Roaming — $10/day [roaming_day_pass_001]"],
            rationale=(
                "The International Roaming 10GB add-on ($60/mo) covers the widest range of countries "
                "and is most cost-effective for trips longer than 6 days. "
                "For shorter trips, Day Pass at $10/day may be cheaper."
            ),
            limitations=["Check if destination country is in the supported list", "Must activate before departure"],
            evidence_ids=[e.id for e in evidence],
        )


def _format_plans(plans: list[dict]) -> str:
    lines = []
    for p in plans:
        data = f"{p['data_gb']} GB" if p["data_gb"] != -1 else "Unlimited"
        lines.append(
            f"- {p['plan_id']}: {p['name']} | ${p['monthly_price_usd']}/mo | "
            f"Data: {data} | Hotspot: {p.get('hotspot_gb', 0)} GB | "
            f"Limitations: {p.get('limitations', 'none')}"
        )
    return "\n".join(lines)


def _format_account(account: dict | None) -> str:
    if not account:
        return "No account data available."
    return (
        f"Current plan: {account.get('current_plan', 'unknown')}\n"
        f"Data used this month: {account.get('monthly_data_used_gb', 'unknown')} GB\n"
        f"Data limit: {account.get('monthly_data_limit_gb', 'unknown')} GB\n"
        f"Devices: {', '.join(account.get('devices', []))}\n"
        f"Upcoming travel: {account.get('upcoming_travel', 'none')}"
    )

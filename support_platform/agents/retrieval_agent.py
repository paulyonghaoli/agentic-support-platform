from __future__ import annotations

from support_platform.data.loaders import DataStore
from support_platform.schemas import Evidence, Intent

# Maps intent to the data sources that are most relevant
_INTENT_SOURCE_MAP: dict[Intent, list[str]] = {
    Intent.BILLING: ["billing_faq", "escalation_policy"],
    Intent.PLAN_RECOMMENDATION: [],  # Plans are handled directly, not as evidence blocks
    Intent.ROAMING: ["roaming_policies", "escalation_policy"],
    Intent.CONNECTIVITY_TROUBLESHOOTING: ["troubleshooting_guides", "escalation_policy"],
    Intent.DEVICE_IOT_ACTIVATION: ["troubleshooting_guides", "escalation_policy"],
    Intent.UNSUPPORTED: ["escalation_policy"],
}

# Extra keywords to inject per intent
_INTENT_KEYWORDS: dict[Intent, list[str]] = {
    Intent.BILLING: ["bill", "charge", "payment", "overage", "refund", "dispute"],
    Intent.PLAN_RECOMMENDATION: ["plan", "data", "unlimited", "family"],
    Intent.ROAMING: ["roaming", "international", "travel", "add-on", "japan", "europe"],
    Intent.CONNECTIVITY_TROUBLESHOOTING: ["signal", "data", "not working", "troubleshoot", "indoor"],
    Intent.DEVICE_IOT_ACTIVATION: ["watch", "smartwatch", "esim", "activate", "device"],
    Intent.UNSUPPORTED: ["escalate", "human", "agent"],
}


class RetrievalAgent:
    def __init__(self, store: DataStore) -> None:
        self._store = store

    def retrieve(self, intent: Intent, message: str) -> list[Evidence]:
        sources = _INTENT_SOURCE_MAP.get(intent, [])
        base_keywords = _INTENT_KEYWORDS.get(intent, [])

        # Supplement with words from the user message (simple tokenization)
        message_words = [w.lower() for w in message.split() if len(w) > 3]
        keywords = list(dict.fromkeys(base_keywords + message_words))  # dedup, preserve order

        raw_results = self._store.search_evidence(keywords, sources if sources else None)

        return [
            Evidence(
                id=r["id"],
                source=r["source"],
                content=r["content"],
                relevance_score=r["relevance_score"],
            )
            for r in raw_results
        ]

    def retrieve_plans(self, tags: list[str] | None = None) -> list[dict]:
        """Return all plans, optionally filtered by tags."""
        if not tags:
            return self._store.plans
        return [p for p in self._store.plans if any(t in p.get("tags", []) for t in tags)]

    def retrieve_account(self, user_id: str) -> dict | None:
        return self._store.get_account(user_id)

    def retrieve_device_info(self, model: str) -> dict | None:
        """Fuzzy match device model across all device categories."""
        model_lower = model.lower()
        for category in ["smartphones", "wearables", "tablets"]:
            for device in self._store.devices.get(category, []):
                if model_lower in device["model"].lower():
                    return device
        return None

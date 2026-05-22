from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load_json(filename: str) -> Any:
    with open(_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def _load_text(filename: str) -> str:
    return (_DATA_DIR / filename).read_text(encoding="utf-8")


class DataStore:
    """Loads and indexes all synthetic data files at startup."""

    def __init__(self) -> None:
        self.plans: list[dict] = _load_json("plans.json")
        self.devices: dict = _load_json("device_compatibility.json")
        self.accounts: list[dict] = _load_json("demo_accounts.json")
        self.roaming_text: str = _load_text("roaming_policies.md")
        self.troubleshooting_text: str = _load_text("troubleshooting_guides.md")
        self.billing_faq_text: str = _load_text("billing_faq.md")
        self.escalation_policy_text: str = _load_text("escalation_policy.md")

        # Pre-parse evidence blocks from markdown files
        self._roaming_evidence = _parse_evidence_blocks(self.roaming_text)
        self._troubleshooting_evidence = _parse_evidence_blocks(self.troubleshooting_text)
        self._billing_evidence = _parse_evidence_blocks(self.billing_faq_text)
        self._escalation_evidence = _parse_evidence_blocks(self.escalation_policy_text)

        # Cache concatenated evidence list — built once, reused on every retrieval call
        self._evidence_cache: list[dict] = (
            self._roaming_evidence
            + self._troubleshooting_evidence
            + self._billing_evidence
            + self._escalation_evidence
        )

        # O(1) account lookup by user_id
        self._accounts_by_id: dict[str, dict] = {
            acc["user_id"]: acc for acc in self.accounts
        }

    def get_account(self, user_id: str) -> dict | None:
        return self._accounts_by_id.get(user_id)

    def get_plan(self, plan_id: str) -> dict | None:
        for plan in self.plans:
            if plan["plan_id"] == plan_id:
                return plan
        return None

    def search_evidence(self, keywords: list[str], sources: list[str] | None = None) -> list[dict]:
        """Return evidence blocks that match any keyword, filtered by source list."""
        all_evidence = self._all_evidence()
        if sources:
            all_evidence = [e for e in all_evidence if e["source"] in sources]

        results = []
        for ev in all_evidence:
            content_lower = ev["content"].lower()
            score = sum(1 for kw in keywords if kw.lower() in content_lower)
            if score > 0:
                results.append({**ev, "relevance_score": min(score / max(len(keywords), 1), 1.0)})

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:5]

    def _all_evidence(self) -> list[dict]:
        return self._evidence_cache


def _parse_evidence_blocks(text: str) -> list[dict]:
    """
    Parse blocks that contain an evidence ID bracket like [SOME_ID_001].
    Each heading/block with an ID becomes a retrievable evidence item.
    """
    blocks: list[dict] = []
    # Split on level-2 or level-3 headings
    sections = re.split(r"\n(?=#{2,3} )", text)
    for section in sections:
        # Look for evidence IDs in format [WORD_WORD_001]
        ids = re.findall(r"\[([A-Z0-9_]+)\]", section)
        if not ids:
            continue
        for ev_id in ids:
            source = _infer_source(ev_id)
            blocks.append({
                "id": ev_id.lower(),
                "source": source,
                "content": section.strip(),
            })
    return blocks


def _infer_source(ev_id: str) -> str:
    ev_id_lower = ev_id.lower()
    if ev_id_lower.startswith("roaming"):
        return "roaming_policies"
    if ev_id_lower.startswith("trouble"):
        return "troubleshooting_guides"
    if ev_id_lower.startswith("billing"):
        return "billing_faq"
    if ev_id_lower.startswith("escalation"):
        return "escalation_policy"
    return "unknown"


# Module-level singleton — loaded once per process
_store: DataStore | None = None


def get_data_store() -> DataStore:
    global _store
    if _store is None:
        _store = DataStore()
    return _store

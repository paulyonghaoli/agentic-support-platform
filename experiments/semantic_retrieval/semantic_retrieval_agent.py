"""
Drop-in replacement for support_platform/agents/retrieval_agent.py
that uses semantic similarity instead of keyword hit-counting.

Usage — swap into the Orchestrator:

    from experiments.semantic_retrieval.semantic_retrieval_agent import (
        SemanticRetrievalAgent,
    )
    self._retrieval = SemanticRetrievalAgent(self._store, client=self._client)

Everything else in the pipeline is unchanged.
"""
from __future__ import annotations

from typing import Optional

from openai import OpenAI

from support_platform.data.loaders import DataStore
from support_platform.schemas import Evidence, Intent

from .embedder import embed_query, load_or_build_embeddings
from .vector_store import VectorStore

# Sources that are relevant per intent — same as the keyword agent
_INTENT_SOURCE_MAP: dict[Intent, list[str]] = {
    Intent.BILLING: ["billing_faq", "escalation_policy"],
    Intent.PLAN_RECOMMENDATION: [],
    Intent.ROAMING: ["roaming_policies", "escalation_policy"],
    Intent.CONNECTIVITY_TROUBLESHOOTING: ["troubleshooting_guides", "escalation_policy"],
    Intent.DEVICE_IOT_ACTIVATION: ["troubleshooting_guides", "escalation_policy"],
    Intent.UNSUPPORTED: ["escalation_policy"],
}


class SemanticRetrievalAgent:
    """
    Retrieves evidence by embedding the user message and finding the most
    semantically similar evidence blocks via cosine similarity.

    Builds the vector index once at construction time. All subsequent queries
    are pure in-memory similarity lookups.
    """

    def __init__(self, store: DataStore, client: Optional[OpenAI] = None) -> None:
        self._store = store
        self._client = client
        self._store_all = VectorStore()
        self._store_by_source: dict[str, VectorStore] = {}
        self._build_index()

    def _build_index(self) -> None:
        docs = self._store._evidence_cache
        print(f"[SemanticRetrievalAgent] Building index for {len(docs)} evidence blocks...")
        embeddings = load_or_build_embeddings(docs, self._client)

        for doc, emb in zip(docs, embeddings):
            self._store_all.add(doc, emb)
            source = doc["source"]
            if source not in self._store_by_source:
                self._store_by_source[source] = VectorStore()
            self._store_by_source[source].add(doc, emb)

        print(f"[SemanticRetrievalAgent] Index ready ({len(self._store_all)} docs).")

    def retrieve(self, intent: Intent, message: str, top_k: int = 5) -> list[Evidence]:
        query_emb = embed_query(message, self._client)
        sources = _INTENT_SOURCE_MAP.get(intent, [])

        if sources:
            # Search within relevant sources, merge results
            candidates: list[tuple[dict, float]] = []
            for source in sources:
                store = self._store_by_source.get(source)
                if store:
                    candidates.extend(store.search(query_emb, top_k=top_k))
            # Re-rank the merged candidates by score and deduplicate by id
            seen: set[str] = set()
            ranked: list[tuple[dict, float]] = []
            for doc, score in sorted(candidates, key=lambda x: x[1], reverse=True):
                if doc["id"] not in seen:
                    seen.add(doc["id"])
                    ranked.append((doc, score))
            results = ranked[:top_k]
        else:
            results = self._store_all.search(query_emb, top_k=top_k)

        return [
            Evidence(
                id=doc["id"],
                source=doc["source"],
                content=doc["content"],
                relevance_score=min(score, 1.0),
            )
            for doc, score in results
        ]

    # Delegate non-retrieval methods to the original store
    def retrieve_plans(self, tags: list[str] | None = None) -> list[dict]:
        if not tags:
            return self._store.plans
        return [p for p in self._store.plans if any(t in p.get("tags", []) for t in tags)]

    def retrieve_account(self, user_id: str) -> dict | None:
        return self._store.get_account(user_id)

    def retrieve_device_info(self, model: str) -> dict | None:
        model_lower = model.lower()
        for category in ["smartphones", "wearables", "tablets"]:
            for device in self._store.devices.get(category, []):
                if model_lower in device["model"].lower():
                    return device
        return None

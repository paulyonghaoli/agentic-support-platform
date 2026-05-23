#!/usr/bin/env python
"""
Benchmark: keyword retrieval vs semantic retrieval.

Runs a set of queries designed to stress the boundary between them,
then shows side-by-side results so you can see where each approach wins.

Usage:
    python experiments/semantic_retrieval/benchmark.py
    python experiments/semantic_retrieval/benchmark.py --no-cache   # force re-embed
    python experiments/semantic_retrieval/benchmark.py --json        # raw output
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from support_platform.data.loaders import get_data_store
from support_platform.schemas import Intent

from .embedder import load_or_build_embeddings, embed_query
from .vector_store import VectorStore

# ---------------------------------------------------------------------------
# Benchmark queries
# Each tuple: (description, message, expected_intent, note_on_challenge)
# ---------------------------------------------------------------------------
QUERIES = [
    (
        "Paraphrase — plain language for connectivity",
        "my phone keeps cutting out inside the house",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        "Keyword misses 'cutting out'. Semantic should match indoor signal guide.",
    ),
    (
        "Location synonym — city instead of country",
        "I'm heading to Tokyo next week, will my phone work?",
        Intent.ROAMING,
        "Keyword: 'Japan' not in message. Semantic: 'Tokyo' is close to Japan/roaming.",
    ),
    (
        "Indirect billing reference",
        "my statement has an unexpected item I don't recognise",
        Intent.BILLING,
        "Keyword: 'statement' not a billing keyword. Semantic: close to billing FAQ.",
    ),
    (
        "Technical jargon — no matching keywords",
        "cellular radio won't lock on to any band",
        Intent.CONNECTIVITY_TROUBLESHOOTING,
        "Zero keyword hits. Semantic should still find troubleshooting guides.",
    ),
    (
        "Exact keyword match — keyword should win",
        "I want a refund for this unauthorized charge on my bill",
        Intent.BILLING,
        "Both should retrieve billing dispute evidence. Checks that semantic matches keyword.",
    ),
    (
        "Wearable using different vocabulary",
        "my smartwatch lost its independent data connection",
        Intent.DEVICE_IOT_ACTIVATION,
        "Keyword: 'smartwatch' matches. Semantic: 'independent data connection' context.",
    ),
    (
        "Roaming failure while abroad — live scenario",
        "I landed in Paris and none of my apps are loading",
        Intent.ROAMING,
        "Keyword: 'Paris' not in map, but 'France'/'Europe' not mentioned. Semantic win.",
    ),
    (
        "Plan question with no plan keywords",
        "what's the cheapest option that includes hotspot?",
        Intent.PLAN_RECOMMENDATION,
        "Keyword: 'hotspot' not in plan keywords. Semantic should find plan content.",
    ),
]


def _build_keyword_results(query: str, intent: Intent, store, top_k: int = 5) -> list[tuple[str, float]]:
    """Replicate current keyword retrieval scoring."""
    from support_platform.agents.retrieval_agent import _INTENT_KEYWORDS, _INTENT_SOURCE_MAP

    sources = _INTENT_SOURCE_MAP.get(intent, [])
    base_keywords = _INTENT_KEYWORDS.get(intent, [])
    message_words = [w.lower() for w in query.split() if len(w) > 3]
    keywords = list(dict.fromkeys(base_keywords + message_words))

    all_evidence = store._evidence_cache
    if sources:
        all_evidence = [e for e in all_evidence if e["source"] in sources]

    results = []
    for ev in all_evidence:
        content_lower = ev["content"].lower()
        score = sum(1 for kw in keywords if kw.lower() in content_lower)
        if score > 0:
            results.append((ev["id"], round(score / max(len(keywords), 1), 3)))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def run_benchmark(client, cache: bool = True) -> list[dict]:
    store = get_data_store()
    docs = store._evidence_cache

    print("\nBuilding semantic index...")
    embeddings = load_or_build_embeddings(docs, client, cache=cache)
    vector_store = VectorStore()
    vector_store.add_batch(docs, embeddings)

    results = []
    for desc, query, intent, note in QUERIES:
        # Keyword retrieval
        kw_results = _build_keyword_results(query, intent, store)

        # Semantic retrieval
        query_emb = embed_query(query, client)
        sem_raw = vector_store.search(query_emb, top_k=5)
        sem_results = [(doc["id"], score) for doc, score in sem_raw]

        results.append({
            "description": desc,
            "query": query,
            "intent": intent.value,
            "note": note,
            "keyword": kw_results,
            "semantic": sem_results,
            "keyword_top1": kw_results[0][0] if kw_results else None,
            "semantic_top1": sem_results[0][0] if sem_results else None,
            "agree": (
                kw_results[0][0] == sem_results[0][0]
                if kw_results and sem_results else False
            ),
        })

    return results


def print_report(results: list[dict]) -> None:
    sep = "-" * 70
    print(f"\n{'=' * 70}")
    print("SEMANTIC vs KEYWORD RETRIEVAL BENCHMARK")
    print(f"{'=' * 70}")

    agreed = sum(1 for r in results if r["agree"])
    print(f"  Queries: {len(results)}   Top-1 agreement: {agreed}/{len(results)}\n")

    for r in results:
        print(sep)
        print(f"  {r['description']}")
        print(f"  Query : \"{r['query']}\"")
        print(f"  Intent: {r['intent']}")
        print(f"  Note  : {r['note']}")
        print()

        kw = r["keyword"]
        sem = r["semantic"]
        max_rows = max(len(kw), len(sem), 3)

        print(f"  {'KEYWORD (hit ratio)':38s}  SEMANTIC (cosine sim)")
        print(f"  {'-' * 36}  {'-' * 28}")
        for i in range(max_rows):
            kw_str = f"{kw[i][0]:35s} {kw[i][1]:.3f}" if i < len(kw) else ""
            sem_str = f"{sem[i][0]:35s} {sem[i][1]:.4f}" if i < len(sem) else ""
            marker = "  " if i > 0 else ("== " if r["agree"] else "!! ")
            print(f"  {marker}{kw_str:38s}  {sem_str}")

        if not kw:
            print(f"  !! KEYWORD: no results")
        if not r["agree"]:
            print(f"\n  ** TOP-1 DIFFERS -- kw={r['keyword_top1']}  sem={r['semantic_top1']}")
        print()

    print(sep)
    print(f"  Top-1 agreement : {agreed}/{len(results)} ({agreed/len(results):.0%})")
    print(f"  Keyword no-match: {sum(1 for r in results if not r['keyword'])} queries returned nothing")
    print(sep)


def main() -> None:
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cache", action="store_true", help="Force re-embedding")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("WARNING: OPENAI_API_KEY not set — using keyword-vector fallback (lower quality).")
        client = None
    else:
        client = OpenAI(api_key=api_key)

    results = run_benchmark(client, cache=not args.no_cache)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results)


if __name__ == "__main__":
    main()

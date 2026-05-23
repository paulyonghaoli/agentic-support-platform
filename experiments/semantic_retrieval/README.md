# Experiment: Semantic Retrieval

**Question:** How much does switching from keyword hit-counting to cosine similarity over text embeddings improve evidence retrieval for a support system?

---

## What the current system does

`support_platform/agents/retrieval_agent.py` retrieves evidence blocks by counting how many pre-defined keywords appear in the evidence content. This works well when the user's phrasing matches the keyword list exactly, but fails on:

- **Paraphrases** — "my internet keeps cutting out" doesn't match `"not working"` or `"disconnected"`
- **Location synonyms** — "heading to Tokyo" doesn't match `"japan"`
- **Domain vocabulary** — "my statement has an unexpected item" doesn't match `"bill"` / `"charge"`
- **Zero-keyword queries** — "cellular radio won't lock on" scores 0 on everything

---

## What this experiment does

1. Embeds all 16 evidence blocks at startup using `text-embedding-3-small`
2. On each query, embeds the user message and finds the top-k blocks by cosine similarity
3. Compares results against the keyword retriever on 8 carefully chosen test queries
4. Highlights where each approach wins and why

The `SemanticRetrievalAgent` is a drop-in replacement for `RetrievalAgent` — same interface, same output type (`list[Evidence]`). Nothing else in the pipeline changes.

---

## Architecture

```
Evidence blocks (16)
        │
        ▼
   Embedder                      ← text-embedding-3-small (or keyword-vector fallback)
        │ float[1536] per block
        ▼
   VectorStore                   ← pure-Python cosine similarity index
        │
        ▼ (at query time)
   embed_query(message)
        │ float[1536]
        ▼
   VectorStore.search(top_k=5)   ← dot-product ranking
        │ list[(doc, score)]
        ▼
   list[Evidence]                ← same schema as keyword retriever
```

---

## Setup

```bash
# From project root
python -m experiments.semantic_retrieval.benchmark

# Force re-embed (ignore cache)
python -m experiments.semantic_retrieval.benchmark --no-cache

# Raw JSON output
python -m experiments.semantic_retrieval.benchmark --json
```

Embeddings are cached in `.embedding_cache.json` next to the benchmark so repeat runs are free. The cache invalidates automatically if any evidence content changes.

---

## Swap into the live pipeline

```python
# In support_platform/orchestrator.py __init__:
from experiments.semantic_retrieval.semantic_retrieval_agent import SemanticRetrievalAgent

self._retrieval = SemanticRetrievalAgent(self._store, client=self._client)
```

Everything else — intent routing, specialist agents, escalation, evaluation — stays unchanged.

---

## Benchmark queries

| Query | Challenge | Who should win |
| --- | --- | --- |
| "my phone keeps cutting out inside the house" | "cutting out" ≠ any keyword | Semantic |
| "I'm heading to Tokyo next week" | "Tokyo" ≠ "japan" keyword | Semantic |
| "my statement has an unexpected item" | "statement" not in billing keywords | Semantic |
| "cellular radio won't lock on to any band" | zero keyword hits | Semantic |
| "I want a refund for this unauthorized charge" | exact keyword match | Both (agreement check) |
| "my smartwatch lost its independent data connection" | "smartwatch" matches but context is rich | Both |
| "I landed in Paris and none of my apps are loading" | "Paris" not in any keyword | Semantic |
| "what's the cheapest option that includes hotspot?" | "hotspot" not in plan keywords | Semantic |

---

## Expected findings

**Semantic wins on:** Any query where the user's vocabulary differs from the keyword list. In a real support system this is the majority of traffic — customers don't know the product taxonomy.

**Keyword wins (or ties) on:** High-signal exact matches where the keyword list was carefully tuned to the domain. Keyword retrieval is also faster, cheaper, and fully deterministic.

**The production answer:** BM25 hybrid (keyword + semantic weighted sum) outperforms either alone. This experiment isolates the semantic half so you can measure its contribution independently.

---

## Key files

| File | Role |
| --- | --- |
| `embedder.py` | OpenAI batch embedding + JSON cache + keyword-vector fallback |
| `vector_store.py` | Pure-Python cosine similarity index — no external deps |
| `semantic_retrieval_agent.py` | Drop-in for `RetrievalAgent` using semantic search |
| `benchmark.py` | Side-by-side comparison of keyword vs semantic results |

---

## What's not in scope here

- **BM25 hybrid** — the natural next step; weight keyword and semantic scores
- **Re-ranker** — a second-pass cross-encoder model to re-rank top-k candidates
- **ANN index** — FAISS / usearch for >10k docs where brute-force cosine is too slow
- **Fine-tuned embeddings** — domain-adapted embeddings trained on support conversations

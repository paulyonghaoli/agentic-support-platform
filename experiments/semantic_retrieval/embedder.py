"""
Embedding generation with a keyword-vector fallback.

When an OpenAI client is available, uses text-embedding-3-small (1536-dim).
When it is not, falls back to a normalized bag-of-words projection so the
rest of the experiment still runs — just with lower quality results.
"""
from __future__ import annotations

import json
import math
import os
from collections import Counter
from pathlib import Path
from typing import Optional

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
_FALLBACK_DIM = 512

_CACHE_FILE = Path(__file__).parent / ".embedding_cache.json"


def embed_texts(texts: list[str], client: Optional[OpenAI]) -> list[list[float]]:
    """
    Embed a batch of texts. Returns a list of float vectors, one per text.
    Falls back to keyword vectors if no client is available.
    """
    if client is None:
        return [_keyword_vector(t) for t in texts]

    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


def embed_query(text: str, client: Optional[OpenAI]) -> list[float]:
    return embed_texts([text], client)[0]


def load_or_build_embeddings(
    docs: list[dict],
    client: Optional[OpenAI],
    cache: bool = True,
) -> list[list[float]]:
    """
    Embed all evidence docs, using a JSON cache to avoid re-embedding on repeat runs.
    Cache key is the doc content, so it automatically rebuilds if content changes.
    """
    contents = [d["content"] for d in docs]

    if cache and _CACHE_FILE.exists():
        cached = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        if cached.get("contents") == contents:
            print(f"  [embedder] Loaded {len(docs)} embeddings from cache.")
            return cached["embeddings"]

    print(f"  [embedder] Embedding {len(docs)} evidence blocks via {EMBEDDING_MODEL}...")
    embeddings = embed_texts(contents, client)

    if cache:
        _CACHE_FILE.write_text(
            json.dumps({"contents": contents, "embeddings": embeddings}),
            encoding="utf-8",
        )
        print(f"  [embedder] Saved to cache ({_CACHE_FILE.name}).")

    return embeddings


def _keyword_vector(text: str) -> list[float]:
    """
    Normalized bag-of-words projected to a fixed-size vector via hashing.
    Used as fallback when no OpenAI client is available.
    Dimension is smaller than real embeddings — similarity quality is lower.
    """
    words = text.lower().split()
    counts = Counter(words)
    vec = [0.0] * _FALLBACK_DIM
    for word, count in counts.items():
        vec[hash(word) % _FALLBACK_DIM] += count
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def is_real_embedding(embedding: list[float]) -> bool:
    return len(embedding) == EMBEDDING_DIM

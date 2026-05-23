"""
In-process vector store using cosine similarity.

Pure Python — no numpy or external vector DB required.
For 16 evidence blocks × 1536 dims this is microseconds per query.
At production scale (10k+ docs) you would swap this for a proper ANN index
(FAISS, usearch, or a managed service like Pinecone).
"""
from __future__ import annotations

import math
from typing import Any


class VectorStore:
    """
    Stores (document, embedding) pairs and answers top-k cosine similarity queries.
    """

    def __init__(self) -> None:
        self._docs: list[dict[str, Any]] = []
        self._embeddings: list[list[float]] = []

    def add(self, doc: dict[str, Any], embedding: list[float]) -> None:
        self._docs.append(doc)
        self._embeddings.append(embedding)

    def add_batch(self, docs: list[dict[str, Any]], embeddings: list[list[float]]) -> None:
        for doc, emb in zip(docs, embeddings):
            self.add(doc, emb)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[tuple[dict, float]]:
        """Return the top_k most similar docs with their cosine similarity scores."""
        if not self._embeddings:
            return []

        scores = [cosine(query_embedding, doc_emb) for doc_emb in self._embeddings]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [(self._docs[i], round(score, 4)) for i, score in ranked[:top_k]]

    def __len__(self) -> int:
        return len(self._docs)


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)

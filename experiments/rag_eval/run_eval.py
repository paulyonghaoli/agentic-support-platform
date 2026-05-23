"""
RAG evaluation using rag-eval-harness.

Runs each eval case through the support platform orchestrator,
collects (question, answer, contexts) and feeds them into the harness
for faithfulness, relevance, precision, and context recall scoring.

Usage:
    python -m experiments.rag_eval.run_eval                  # keyword retriever (baseline)
    python -m experiments.rag_eval.run_eval --semantic        # semantic retriever
    python -m experiments.rag_eval.run_eval --compare         # run both and print side-by-side delta
    python -m experiments.rag_eval.run_eval --method cosine   # change faithfulness method
    python -m experiments.rag_eval.run_eval --json            # raw JSON output
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(override=True)

from openai import OpenAI
from evaluator.types import EvalRecord
from evaluator.pipeline import run_evaluation

from support_platform.data.loaders import get_data_store
from support_platform.orchestrator import Orchestrator
from support_platform.schemas import SupportRequest

from .eval_cases import EVAL_CASES

_OUT_DIR = Path(__file__).parent / "output"
_METRIC_ORDER = ["faithfulness", "relevance", "precision", "context_relevance", "recall"]
_METRIC_LABELS = {
    "faithfulness":      "Faithfulness      (answer supported by context)",
    "relevance":         "Answer Relevance  (answer addresses the question)",
    "precision":         "Context Precision (retrieved chunks are useful)",
    "context_relevance": "Context Relevance (chunks are semantically close)",
    "recall":            "Context Recall    (chunks contain the answer)",
}


def _swap_semantic_retriever(orchestrator: Orchestrator, client: OpenAI) -> None:
    from experiments.semantic_retrieval.semantic_retrieval_agent import SemanticRetrievalAgent
    orchestrator._retrieval = SemanticRetrievalAgent(orchestrator._store, client=client)


def _collect_records(orchestrator: Orchestrator) -> list[EvalRecord]:
    store = get_data_store()
    evidence_by_id = {ev["id"]: ev["content"] for ev in store._evidence_cache}

    records = []
    for case in EVAL_CASES:
        req = SupportRequest(user_id=case.user_id, message=case.question)
        resp = orchestrator.handle(req)
        contexts = [evidence_by_id[eid] for eid in resp.evidence_ids if eid in evidence_by_id]
        records.append(
            EvalRecord(
                question=case.question,
                answer=resp.answer,
                contexts=contexts,
                ground_truth=case.ground_truth,
            )
        )
        print(f"  [{resp.intent:30s}] {case.question[:58]}")

    return records


def _write_jsonl(records: list[EvalRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(
                json.dumps({
                    "question": r.question,
                    "answer": r.answer,
                    "contexts": r.contexts,
                    "ground_truth": r.ground_truth,
                })
                + "\n"
            )


def _run_one(label: str, records: list[EvalRecord], config: dict) -> dict:
    out_dir = _OUT_DIR / label
    jsonl_path = out_dir / "records.jsonl"
    _write_jsonl(records, jsonl_path)

    faithfulness_method = config.get("faithfulness_method", "nli")
    use_llm = config.get("llm_as_judge", {}).get("enabled", False)
    print(f"\nScoring [{label}] — faithfulness={faithfulness_method}, llm_judge={use_llm}...")
    summary = run_evaluation(jsonl_path, out_dir, config)
    return summary


def _print_summary(label: str, summary: dict, n: int) -> None:
    metrics = summary.get("metrics", {})
    print(f"\n{'=' * 62}")
    print(f"  {label.upper()}")
    print(f"  Records: {n}")
    print(f"{'=' * 62}")
    for key in _METRIC_ORDER:
        m = metrics.get(key)
        if m is None:
            continue
        mean = m.get("mean", 0.0)
        bar = "#" * int(mean * 30) + "-" * (30 - int(mean * 30))
        print(f"  {_METRIC_LABELS[key]}")
        print(f"    [{bar}] {mean:.3f}")
        print()


def _print_comparison(kw_summary: dict, sem_summary: dict, n: int) -> None:
    kw_m = kw_summary.get("metrics", {})
    sem_m = sem_summary.get("metrics", {})

    print(f"\n{'=' * 72}")
    print("  KEYWORD vs SEMANTIC — DELTA")
    print(f"  Records: {n}")
    print(f"{'=' * 72}")
    print(f"  {'Metric':<36}  {'Keyword':>8}  {'Semantic':>8}  {'Delta':>8}")
    print(f"  {'-' * 36}  {'-' * 8}  {'-' * 8}  {'-' * 8}")

    for key in _METRIC_ORDER:
        kw = (kw_m.get(key) or {}).get("mean")
        sem = (sem_m.get(key) or {}).get("mean")
        if kw is None and sem is None:
            continue
        kw = kw or 0.0
        sem = sem or 0.0
        delta = sem - kw
        arrow = "+" if delta > 0.01 else ("-" if delta < -0.01 else " ")
        label = _METRIC_LABELS[key].split("(")[0].strip()
        print(f"  {label:<36}  {kw:>8.3f}  {sem:>8.3f}  {arrow}{abs(delta):>7.3f}")

    print(f"{'=' * 72}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true", help="Use semantic retriever")
    parser.add_argument("--compare", action="store_true", help="Run both retrievers and compare")
    parser.add_argument(
        "--method", choices=["cosine", "nli", "llm"], default="nli",
        help="Faithfulness scoring method (default: nli)",
    )
    parser.add_argument("--json", action="store_true", help="Print raw JSON scores")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None

    use_llm = args.method == "llm"
    faithfulness_method = "cosine" if args.method == "cosine" else "nli"
    config = {
        "faithfulness_method": faithfulness_method,
        "llm_as_judge": {"enabled": use_llm},
        "similarity_threshold": 0.5,
        "top_k": 5,
    }

    if args.compare:
        print("\n=== KEYWORD RETRIEVER ===")
        print("Initialising orchestrator (keyword)...")
        kw_orch = Orchestrator()
        print(f"\nRunning {len(EVAL_CASES)} eval cases:")
        kw_records = _collect_records(kw_orch)
        kw_summary = _run_one("keyword", kw_records, config)

        print("\n=== SEMANTIC RETRIEVER ===")
        print("Initialising orchestrator (semantic)...")
        sem_orch = Orchestrator()
        _swap_semantic_retriever(sem_orch, client)
        print(f"\nRunning {len(EVAL_CASES)} eval cases:")
        sem_records = _collect_records(sem_orch)
        sem_summary = _run_one("semantic", sem_records, config)

        if args.json:
            print(json.dumps({"keyword": kw_summary, "semantic": sem_summary}, indent=2))
        else:
            _print_comparison(kw_summary, sem_summary, len(EVAL_CASES))
        return

    # Single retriever run
    print("\nInitialising orchestrator...")
    orchestrator = Orchestrator()
    label = "keyword"

    if args.semantic:
        print("[SemanticRetrievalAgent] Swapping in semantic retriever...")
        _swap_semantic_retriever(orchestrator, client)
        label = "semantic"

    print(f"\nRunning {len(EVAL_CASES)} eval cases [{label}]:")
    records = _collect_records(orchestrator)
    summary = _run_one(label, records, config)

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        _print_summary(label, summary, len(EVAL_CASES))
        out_dir = _OUT_DIR / label
        print(f"  Full report : {out_dir / 'report.md'}")
        print(f"  Raw scores  : {out_dir / 'scores.jsonl'}")


if __name__ == "__main__":
    main()

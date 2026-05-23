"""
RAG evaluation using rag-eval-harness.

Runs each eval case through the support platform orchestrator,
collects (question, answer, contexts) and feeds them into the harness
for faithfulness, relevance, precision, and context recall scoring.

Usage:
    python -m experiments.rag_eval.run_eval
    python -m experiments.rag_eval.run_eval --method cosine
    python -m experiments.rag_eval.run_eval --method llm
    python -m experiments.rag_eval.run_eval --json
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


def _collect_records(orchestrator: Orchestrator) -> list[EvalRecord]:
    """Run every eval case through the orchestrator and build EvalRecord objects."""
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
        print(f"  [{resp.intent:30s}] {case.question[:60]}")

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--method",
        choices=["cosine", "nli", "llm"],
        default="nli",
        help="Faithfulness scoring method (default: nli)",
    )
    parser.add_argument("--json", action="store_true", help="Print raw JSON scores")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key) if api_key else None

    print("\nInitialising orchestrator...")
    orchestrator = Orchestrator()

    print(f"\nRunning {len(EVAL_CASES)} eval cases through the pipeline:")
    records = _collect_records(orchestrator)

    out_dir = Path(__file__).parent / "output"
    jsonl_path = out_dir / "records.jsonl"
    _write_jsonl(records, jsonl_path)
    print(f"\nWrote {len(records)} records to {jsonl_path}")

    use_llm = args.method == "llm"
    faithfulness_method = "cosine" if args.method == "cosine" else "nli"

    config = {
        "faithfulness_method": faithfulness_method,
        "llm_as_judge": {"enabled": use_llm},
        "similarity_threshold": 0.5,
        "top_k": 5,
    }

    print(f"\nRunning rag-eval-harness (faithfulness={faithfulness_method}, llm_judge={use_llm})...")
    summary = run_evaluation(jsonl_path, out_dir, config)

    if args.json:
        print(json.dumps(summary, indent=2))
        return

    # Pretty print
    metrics = summary.get("metrics", {})
    print(f"\n{'=' * 60}")
    print("RAG EVAL RESULTS")
    print(f"{'=' * 60}")
    print(f"  Records evaluated : {summary.get('total_records', len(records))}")
    print()

    order = ["faithfulness", "relevance", "precision", "context_relevance", "recall"]
    labels = {
        "faithfulness":       "Faithfulness       (answer supported by context)",
        "relevance":          "Answer Relevance   (answer addresses the question)",
        "precision":          "Context Precision  (retrieved chunks are useful)",
        "context_relevance":  "Context Relevance  (chunks are close to question)",
        "recall":             "Context Recall     (chunks contain the answer — needs ground truth)",
    }

    for key in order:
        m = metrics.get(key)
        if m is None:
            continue
        mean = m.get("mean", 0.0)
        bar_len = int(mean * 30)
        bar = "#" * bar_len + "-" * (30 - bar_len)
        print(f"  {labels[key]}")
        print(f"    [{bar}] {mean:.3f}  (min {m.get('min', 0):.3f} / max {m.get('max', 0):.3f})")
        print()

    report_path = out_dir / "report.md"
    if report_path.exists():
        print(f"  Full report: {report_path}")
    print(f"  Raw scores : {out_dir / 'scores.jsonl'}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

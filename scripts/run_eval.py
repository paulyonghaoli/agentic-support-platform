#!/usr/bin/env python
"""
Evaluation harness for the Agentic Support Platform.

Runs a fixed set of test cases through the orchestrator and reports
aggregate metrics: success rate, escalation accuracy, average
groundedness, and fallback rate.

Usage:
    python scripts/run_eval.py
    python scripts/run_eval.py --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the project root is on the path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from support_platform.orchestrator import Orchestrator
from support_platform.schemas import SupportRequest

# ---------------------------------------------------------------------------
# Eval cases
# ---------------------------------------------------------------------------
# Each case defines:
#   message, user_id, expected_intent, expect_escalation, description,
#   check_fn (optional): called with the response to perform additional checks

EVAL_CASES = [
    {
        "id": "EVAL-001",
        "description": "Plan recommendation for family with high usage",
        "message": "My family uses around 80GB per month. Should we change plans?",
        "user_id": "demo_user_002",
        "expected_intent": "plan_recommendation",
        "expect_escalation": False,
        "check_fn": lambda r: "family" in r.answer.lower() or "unlimited" in r.answer.lower(),
    },
    {
        "id": "EVAL-002",
        "description": "Roaming recommendation for Japan trip",
        "message": "I'm traveling to Japan next week. What roaming option do I need?",
        "user_id": "demo_user_001",
        "expected_intent": "roaming",
        "expect_escalation": False,
        "check_fn": lambda r: len(r.evidence_ids) > 0 and "japan" in r.answer.lower(),
    },
    {
        "id": "EVAL-003",
        "description": "Connectivity troubleshooting with missing slot",
        "message": "My mobile data is not working.",
        "user_id": "demo_user_001",
        "expected_intent": "connectivity_troubleshooting",
        "expect_escalation": False,
        "check_fn": lambda r: "?" in r.answer or "step" in r.answer.lower(),
    },
    {
        "id": "EVAL-004",
        "description": "Data not working after plan change — steps provided",
        "message": "My mobile data stopped working after I changed plans.",
        "user_id": "demo_user_003",  # recent_plan_change=True
        "expected_intent": "connectivity_troubleshooting",
        "expect_escalation": False,
        "check_fn": lambda r: "airplane" in r.answer.lower() or "apn" in r.answer.lower() or "restart" in r.answer.lower(),
    },
    {
        "id": "EVAL-005",
        "description": "Billing issue requiring escalation — refund request",
        "message": "I want a refund for this unauthorized charge on my account.",
        "user_id": "demo_user_002",
        "expected_intent": "billing",
        "expect_escalation": True,
        "check_fn": lambda r: "agent" in r.answer.lower() or "escalat" in r.answer.lower(),
    },
    {
        "id": "EVAL-006",
        "description": "Unsupported request — should escalate",
        "message": "Can you access my neighbor's account to check something?",
        "user_id": "demo_user_001",
        "expected_intent": "unsupported",
        "expect_escalation": True,
        "check_fn": lambda r: r.escalation is True,
    },
    {
        "id": "EVAL-007",
        "description": "Repeated connectivity failure — should escalate",
        "message": "I keep losing signal indoors.",
        "user_id": "demo_user_004",  # 4 connectivity tickets in 90 days
        "expected_intent": "connectivity_troubleshooting",
        "expect_escalation": True,
        "check_fn": lambda r: r.escalation is True,
    },
    {
        "id": "EVAL-008",
        "description": "Proactive support trigger — data nearly exhausted",
        "message": "Can you tell me about my current data plan?",
        "user_id": "demo_user_001",  # 96% data used, upcoming Japan trip
        "expected_intent": "plan_recommendation",
        "expect_escalation": False,
        "check_fn": lambda r: r.proactive_signals is not None and len(r.proactive_signals) > 0,
    },
    {
        "id": "EVAL-009",
        "description": "Grounded response with evidence IDs — roaming",
        "message": "What are my options for roaming in Europe?",
        "user_id": "demo_user_001",
        "expected_intent": "roaming",
        "expect_escalation": False,
        "check_fn": lambda r: len(r.evidence_ids) > 0 and r.evaluation.groundedness >= 0.4,
    },
    {
        "id": "EVAL-010",
        "description": "Trace event generation — full pipeline",
        "message": "Which plan should I get for heavy data use?",
        "user_id": "demo_user_003",
        "expected_intent": "plan_recommendation",
        "expect_escalation": False,
        "check_fn": lambda r: len(r.trace) >= 5,
    },
    {
        "id": "EVAL-011",
        "description": "Smartwatch activation — asks follow-up",
        "message": "My smartwatch is not connecting.",
        "user_id": "demo_user_005",
        "expected_intent": "device_iot_activation",
        "expect_escalation": False,
        "check_fn": lambda r: "?" in r.answer or "watch" in r.answer.lower(),
    },
    {
        "id": "EVAL-012",
        "description": "Bill higher this month — billing FAQ",
        "message": "Why is my bill higher this month?",
        "user_id": "demo_user_002",
        "expected_intent": "billing",
        "expect_escalation": False,
        "check_fn": lambda r: "bill" in r.answer.lower() or "charge" in r.answer.lower(),
    },
]


def run_eval(verbose: bool = False) -> dict:
    results = []

    from support_platform.session.store import get_session_store

    orchestrator = Orchestrator()
    session_store = get_session_store()

    for case in EVAL_CASES:
        # Clear any prior session for this user so cases are isolated
        session_store.clear(case["user_id"])
        request = SupportRequest(
            message=case["message"],
            user_id=case["user_id"],
        )
        response = orchestrator.handle(request)

        intent_correct = (
            case["expected_intent"] is None
            or response.intent == case["expected_intent"]
        )
        escalation_correct = response.escalation == case["expect_escalation"]

        check_fn = case.get("check_fn")
        check_passed = check_fn(response) if check_fn else True

        success = intent_correct and escalation_correct and check_passed

        result = {
            "id": case["id"],
            "description": case["description"],
            "success": success,
            "intent_correct": intent_correct,
            "escalation_correct": escalation_correct,
            "check_passed": check_passed,
            "actual_intent": response.intent,
            "actual_escalation": response.escalation,
            "groundedness": response.evaluation.groundedness,
            "fallback_risk": response.evaluation.fallback_risk,
            "evidence_count": len(response.evidence_ids),
            "trace_event_count": len(response.trace),
        }
        results.append(result)

        if verbose:
            status = "PASS" if success else "FAIL"
            print(f"  [{status}] {case['id']}: {case['description']}")
            if not success:
                print(f"         intent_correct={intent_correct}, escalation_correct={escalation_correct}, check={check_passed}")

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    escalation_correct = sum(1 for r in results if r["escalation_correct"])
    avg_groundedness = sum(r["groundedness"] for r in results) / total
    fallback_high = sum(1 for r in results if r["fallback_risk"] == "high")

    metrics = {
        "total_cases": total,
        "passed": passed,
        "success_rate": round(passed / total, 3),
        "escalation_accuracy": round(escalation_correct / total, 3),
        "average_groundedness": round(avg_groundedness, 3),
        "fallback_rate_high": round(fallback_high / total, 3),
        "case_results": results,
    }
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run evaluation harness")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--verbose", action="store_true", help="Show per-case results")
    args = parser.parse_args()

    print("Running evaluation harness...\n")
    metrics = run_eval(verbose=not args.json or args.verbose)

    if args.json:
        print(json.dumps(metrics, indent=2))
        return

    sep = "-" * 50
    print(f"\n{sep}")
    print("EVALUATION RESULTS")
    print(sep)
    print(f"  Total cases:          {metrics['total_cases']}")
    print(f"  Passed:               {metrics['passed']} / {metrics['total_cases']}")
    print(f"  Success rate:         {metrics['success_rate']:.1%}")
    print(f"  Escalation accuracy:  {metrics['escalation_accuracy']:.1%}")
    print(f"  Avg groundedness:     {metrics['average_groundedness']:.2f}")
    print(f"  High fallback rate:   {metrics['fallback_rate_high']:.1%}")
    print(f"{sep}\n")

    if metrics["success_rate"] < 0.75:
        print("WARNING: Success rate below 75%. Review failed cases.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()

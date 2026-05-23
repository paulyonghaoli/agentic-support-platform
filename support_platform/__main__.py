"""CLI entry point: python -m support_platform "<message>" [--user USER_ID] [--debug]"""
from __future__ import annotations

import argparse
import json
import sys

from dotenv import load_dotenv

load_dotenv(override=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="support_platform",
        description="Agentic Support Platform CLI",
    )
    parser.add_argument("message", nargs="?", help="Support message")
    parser.add_argument("--user", default="demo_user_001", help="User ID (default: demo_user_001)")
    parser.add_argument("--debug", action="store_true", help="Show full trace")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    if not args.message:
        parser.print_help()
        sys.exit(0)

    from support_platform.orchestrator import get_orchestrator
    from support_platform.schemas import SupportRequest

    request = SupportRequest(message=args.message, user_id=args.user, debug=args.debug)
    orchestrator = get_orchestrator()
    response = orchestrator.handle(request)

    if args.json:
        print(json.dumps(response.model_dump(), indent=2, default=str))
        return

    _print_response(response, args.debug)


def _print_response(response, debug: bool) -> None:
    sep = "-" * 60
    print(f"\n{sep}")
    print("ANSWER")
    print(sep)
    print(response.answer)

    print(f"\n{sep}")
    print("SUPPORT DETAILS")
    print(sep)
    print(f"  Intent:          {response.intent}")
    print(f"  Agent path:      {' -> '.join(response.agent_path)}")
    print(f"  Evidence used:   {', '.join(response.evidence_ids) or 'none'}")
    print(f"  Escalation:      {'YES — ' + (response.escalation_reason or '') if response.escalation else 'No'}")

    print(f"\n{sep}")
    print("EVALUATION")
    print(sep)
    ev = response.evaluation
    print(f"  Groundedness:         {ev.groundedness:.2f}")
    print(f"  Completeness:         {ev.completeness:.2f}")
    print(f"  User success:         {ev.user_success_likelihood:.2f}")
    print(f"  Safety correctness:   {ev.safety_correctness:.2f}")
    print(f"  Fallback risk:        {ev.fallback_risk}")
    print(f"  Latency:              {ev.latency_category}")

    if response.proactive_signals:
        print(f"\n{sep}")
        print("PROACTIVE SIGNALS")
        print(sep)
        for sig in response.proactive_signals:
            print(f"  • {sig}")

    if debug and response.trace:
        print(f"\n{sep}")
        print("TRACE")
        print(sep)
        for event in response.trace:
            print(f"  [{event.event_type}] {event.reason}")

    print(f"\n{sep}\n")


if __name__ == "__main__":
    main()

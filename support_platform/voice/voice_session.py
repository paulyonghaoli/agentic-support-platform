"""
Voice interface for the support platform.

Wraps the existing support pipeline:
    audio → transcribe → handle() → synthesize → audio

CLI:
    python -m support_platform.voice path/to/audio.wav --user demo_user_001
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)


def run_voice_pipeline(
    audio_path: str,
    user_id: str = "anonymous",
    debug: bool = False,
) -> dict:
    """
    Core voice pipeline: transcribe → support → synthesize.
    Returns a dict with transcript, answer, audio_path, intent, escalation, trace.
    """
    from support_platform.orchestrator import get_orchestrator
    from support_platform.schemas import SupportRequest
    from support_platform.voice.speech_to_text import transcribe
    from support_platform.voice.text_to_speech import synthesize

    # 1. Transcribe
    transcript = transcribe(audio_path)

    # 2. Run through existing support pipeline (no duplication)
    request = SupportRequest(message=transcript, user_id=user_id, debug=debug)
    orchestrator = get_orchestrator()
    response = orchestrator.handle(request)

    # 3. Synthesize the answer
    audio_out = synthesize(response.answer)

    return {
        "transcript": transcript,
        "answer": response.answer,
        "audio_path": audio_out,
        "intent": response.intent,
        "agent_path": response.agent_path,
        "evidence_ids": response.evidence_ids,
        "escalation": response.escalation,
        "escalation_reason": response.escalation_reason,
        "evaluation": response.evaluation.model_dump(),
        "trace": [e.model_dump() for e in response.trace],
        "session_state_summary": (
            response.session_state_summary.model_dump()
            if response.session_state_summary else None
        ),
        "proactive_signals": response.proactive_signals,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="support_platform.voice",
        description="Voice interface for the Agentic Support Platform",
    )
    parser.add_argument("audio", help="Path to audio file (WAV, MP3, M4A, etc.)")
    parser.add_argument("--user", default="anonymous", help="User ID")
    parser.add_argument("--debug", action="store_true", help="Show full trace")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    audio_path = args.audio
    if not Path(audio_path).exists():
        print(f"Error: audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)

    result = run_voice_pipeline(audio_path, user_id=args.user, debug=args.debug)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return

    sep = "-" * 60
    print(f"\n{sep}")
    print("TRANSCRIPT")
    print(sep)
    print(f"  {result['transcript']}")
    print(f"\n{sep}")
    print("ANSWER")
    print(sep)
    print(result["answer"])
    print(f"\n{sep}")
    print("DETAILS")
    print(sep)
    print(f"  Intent:       {result['intent']}")
    print(f"  Escalation:   {'YES' if result['escalation'] else 'No'}")
    print(f"  Audio output: {result['audio_path']}")

    if args.debug and result.get("trace"):
        print(f"\n{sep}")
        print("TRACE")
        print(sep)
        for event in result["trace"]:
            print(f"  [{event['event_type']}] {event['reason']}")

    print(f"\n{sep}\n")


if __name__ == "__main__":
    main()

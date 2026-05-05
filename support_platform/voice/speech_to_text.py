from __future__ import annotations

import os
from pathlib import Path


def transcribe(audio_file_path: str | Path, client=None) -> str:
    """
    Transcribe audio to text using OpenAI Whisper.
    Falls back to a mock transcript if no API key is available.
    """
    if client is None:
        client = _build_client()

    if client is None:
        return _mock_transcribe(audio_file_path)

    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
        )

    # whisper-1 with response_format="text" returns a string directly
    return result.strip() if isinstance(result, str) else result.text.strip()


def _build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def _mock_transcribe(audio_file_path: str | Path) -> str:
    """
    Mock transcription for testing without an API key.
    Returns a placeholder based on the filename.
    """
    name = Path(audio_file_path).stem.lower()
    if "roaming" in name or "japan" in name:
        return "I am traveling to Japan next week. What roaming option do I need?"
    if "bill" in name:
        return "Why is my bill higher this month?"
    if "data" in name or "connectivity" in name:
        return "My mobile data stopped working."
    if "watch" in name or "device" in name:
        return "My smartwatch is not connecting to cellular."
    return f"[mock transcript for: {Path(audio_file_path).name}]"

from __future__ import annotations

import os
import tempfile
from pathlib import Path


_DEFAULT_VOICE = "nova"
_DEFAULT_MODEL = "tts-1"
_STUB_MARKER = "[voice-stub]"


def synthesize(text: str, output_path: str | Path | None = None, client=None) -> str:
    """
    Synthesize text to speech using OpenAI TTS.
    Returns the path to the output audio file.

    Falls back to a stub (plain text file) when no API key is available.
    The stub path ends with .txt so callers can detect stub mode.
    """
    if output_path is None:
        suffix = ".mp3"
        tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False, prefix="tts_")
        output_path = tmp.name
        tmp.close()

    output_path = str(output_path)

    if client is None:
        client = _build_client()

    if client is None:
        return _stub_synthesize(text, output_path)

    try:
        response = client.audio.speech.create(
            model=_DEFAULT_MODEL,
            voice=_DEFAULT_VOICE,
            input=text,
        )
        response.stream_to_file(output_path)
        return output_path
    except Exception:
        return _stub_synthesize(text, output_path)


def is_stub(audio_path: str) -> bool:
    """Returns True if the audio path is a stub text file rather than real audio."""
    return audio_path.endswith(".txt")


def _build_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def _stub_synthesize(text: str, output_path: str) -> str:
    stub_path = output_path.replace(".mp3", ".txt").replace(".wav", ".txt")
    Path(stub_path).write_text(f"{_STUB_MARKER}\n{text}", encoding="utf-8")
    return stub_path

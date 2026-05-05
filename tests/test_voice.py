from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Speech-to-text tests (mock mode — no real API call)
# ---------------------------------------------------------------------------

def test_stt_mock_returns_string(tmp_path):
    from support_platform.voice.speech_to_text import _mock_transcribe

    audio = tmp_path / "test.wav"
    audio.write_bytes(b"\x00" * 100)
    result = _mock_transcribe(str(audio))
    assert isinstance(result, str)
    assert len(result) > 0


def test_stt_mock_roaming_keyword(tmp_path):
    from support_platform.voice.speech_to_text import _mock_transcribe

    audio = tmp_path / "roaming_query.wav"
    audio.write_bytes(b"\x00" * 100)
    result = _mock_transcribe(str(audio))
    assert "japan" in result.lower() or "roaming" in result.lower()


def test_stt_mock_billing_keyword(tmp_path):
    from support_platform.voice.speech_to_text import _mock_transcribe

    audio = tmp_path / "bill_question.wav"
    audio.write_bytes(b"\x00" * 100)
    result = _mock_transcribe(str(audio))
    assert "bill" in result.lower()


def test_stt_raises_for_missing_file():
    from support_platform.voice.speech_to_text import transcribe

    with pytest.raises(FileNotFoundError):
        transcribe("/nonexistent/path/audio.wav", client=None)


def test_stt_transcribe_uses_mock_when_no_client(tmp_path):
    """When _build_client returns None, transcribe falls back to mock."""
    from support_platform.voice.speech_to_text import transcribe

    audio = tmp_path / "test.wav"
    audio.write_bytes(b"\x00" * 100)
    # Patch _build_client to return None, forcing mock path
    with patch("support_platform.voice.speech_to_text._build_client", return_value=None):
        result = transcribe(str(audio), client=None)
    assert isinstance(result, str)
    assert len(result) > 0


# ---------------------------------------------------------------------------
# Text-to-speech tests (stub mode — no real API call)
# ---------------------------------------------------------------------------

def test_tts_stub_creates_file(tmp_path):
    from support_platform.voice.text_to_speech import synthesize

    out = synthesize("Hello, this is a test.", output_path=str(tmp_path / "out.mp3"), client=None)
    assert Path(out).exists()


def test_tts_stub_file_contains_text(tmp_path):
    from support_platform.voice.text_to_speech import synthesize

    text = "Your bill may be higher due to roaming charges."
    out = synthesize(text, output_path=str(tmp_path / "out.mp3"), client=None)
    content = Path(out).read_text(encoding="utf-8")
    assert text in content


def test_tts_stub_is_detected(tmp_path):
    from support_platform.voice.text_to_speech import synthesize, is_stub

    out = synthesize("Test", output_path=str(tmp_path / "out.mp3"), client=None)
    assert is_stub(out)


def test_tts_non_stub_not_detected():
    from support_platform.voice.text_to_speech import is_stub

    assert not is_stub("/some/path/audio.mp3")


def test_tts_default_output_path_generated():
    from support_platform.voice.text_to_speech import synthesize

    out = synthesize("Test auto path", client=None)
    assert Path(out).exists()
    Path(out).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Voice pipeline integration tests (patched STT/TTS — no real API calls)
# ---------------------------------------------------------------------------

def _make_fake_audio(tmp_path, name="roaming_query.wav"):
    audio = tmp_path / name
    audio.write_bytes(b"\x00" * 100)
    return str(audio)


@patch("support_platform.voice.speech_to_text.transcribe",
       return_value="I'm traveling to Japan next week. What roaming option do I need?")
@patch("support_platform.voice.text_to_speech.synthesize",
       return_value="/tmp/tts_out.txt")
def test_voice_pipeline_returns_required_fields(mock_tts, mock_stt, tmp_path):
    from support_platform.voice.voice_session import run_voice_pipeline

    result = run_voice_pipeline(_make_fake_audio(tmp_path), user_id="demo_user_001")
    assert "transcript" in result
    assert "answer" in result
    assert "audio_path" in result
    assert "intent" in result
    assert "escalation" in result
    assert "trace" in result


@patch("support_platform.voice.speech_to_text.transcribe",
       return_value="I'm traveling to Japan next week. What roaming option do I need?")
@patch("support_platform.voice.text_to_speech.synthesize",
       return_value="/tmp/tts_out.txt")
def test_voice_pipeline_transcript_not_empty(mock_tts, mock_stt, tmp_path):
    from support_platform.voice.voice_session import run_voice_pipeline

    result = run_voice_pipeline(_make_fake_audio(tmp_path), user_id="demo_user_001")
    assert isinstance(result["transcript"], str)
    assert len(result["transcript"]) > 0


@patch("support_platform.voice.speech_to_text.transcribe",
       return_value="Why is my bill higher this month?")
@patch("support_platform.voice.text_to_speech.synthesize",
       return_value="/tmp/tts_out.txt")
def test_voice_pipeline_answer_not_empty(mock_tts, mock_stt, tmp_path):
    from support_platform.voice.voice_session import run_voice_pipeline

    result = run_voice_pipeline(_make_fake_audio(tmp_path, "bill_question.wav"), user_id="demo_user_002")
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0


@patch("support_platform.voice.speech_to_text.transcribe",
       return_value="I'm traveling to Japan next week. What roaming option do I need?")
@patch("support_platform.voice.text_to_speech.synthesize",
       return_value="/tmp/tts_out.txt")
def test_voice_pipeline_intent_is_valid(mock_tts, mock_stt, tmp_path):
    from support_platform.voice.voice_session import run_voice_pipeline

    result = run_voice_pipeline(_make_fake_audio(tmp_path), user_id="demo_user_001")
    valid_intents = {
        "billing", "plan_recommendation", "roaming",
        "connectivity_troubleshooting", "device_iot_activation", "unsupported",
    }
    assert result["intent"] in valid_intents


@patch("support_platform.voice.speech_to_text.transcribe",
       return_value="I'm traveling to Japan next week. What roaming option do I need?")
@patch("support_platform.voice.text_to_speech.synthesize",
       return_value="/tmp/tts_out.txt")
def test_voice_api_endpoint(mock_tts, mock_stt, tmp_path):
    """Integration test for /voice-support API endpoint."""
    import io
    from fastapi.testclient import TestClient
    from support_platform.api import app

    client = TestClient(app)
    fake_audio = io.BytesIO(b"\x00" * 100)
    response = client.post(
        "/voice-support",
        data={"user_id": "demo_user_001", "debug": "false"},
        files={"audio": ("roaming_query.wav", fake_audio, "audio/wav")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "transcript" in data
    assert "answer" in data
    assert "audio_path" in data

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from support_platform.orchestrator import get_orchestrator
from support_platform.schemas import SupportRequest, SupportResponse

app = FastAPI(
    title="Agentic Support Platform",
    description="Enterprise-style AI customer support platform with bounded agentic components.",
    version="0.2.0",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "agentic-support-platform"}


@app.post("/support", response_model=SupportResponse)
def support(request: SupportRequest) -> SupportResponse:
    try:
        orchestrator = get_orchestrator()
        return orchestrator.handle(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/voice-support")
async def voice_support(
    audio: UploadFile = File(..., description="Audio file (WAV, MP3, M4A, etc.)"),
    user_id: str = Form(default="anonymous"),
    debug: bool = Form(default=False),
) -> dict:
    """
    Accept audio, transcribe it, run through the support pipeline, and synthesize the answer.
    The same pipeline as /support — voice is a thin wrapper, not separate logic.
    """
    try:
        suffix = Path(audio.filename or "audio.wav").suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        from support_platform.voice.voice_session import run_voice_pipeline
        result = run_voice_pipeline(tmp_path, user_id=user_id, debug=debug)
        Path(tmp_path).unlink(missing_ok=True)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

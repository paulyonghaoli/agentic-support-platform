from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from support_platform.orchestrator import get_orchestrator
from support_platform.schemas import SupportRequest, SupportResponse

app = FastAPI(
    title="Agentic Support Platform",
    description="Enterprise-style AI customer support platform with bounded agentic components.",
    version="0.1.0",
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

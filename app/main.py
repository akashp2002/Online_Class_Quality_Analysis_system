from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field

from app.services.evaluation import analyze_transcript
from app.services.transcript import parse_transcript, TranscriptError


MAX_TRANSCRIPT_CHARACTERS = 100_000

app = FastAPI(title="Humaniti Class Quality Prototype")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


class AnalysisRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=MAX_TRANSCRIPT_CHARACTERS)
    transcript_format: str = Field(default="text", pattern="^(text|vtt)$")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyses")
async def create_analysis(request: AnalysisRequest) -> dict:
    try:
        segments = parse_transcript(request.transcript, request.transcript_format)
    except TranscriptError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    report = analyze_transcript(segments)
    report["analysis_id"] = str(uuid4())
    report["created_at"] = datetime.now(timezone.utc).isoformat()
    return report

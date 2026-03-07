from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from .job_manager import JobManager
from .models import JobCreateResponse, JobStatusResponse, LentessPayload, RecetasPayload

# Cuando corre como .exe, los logs van junto al ejecutable
if os.environ.get("CIRUGIAS_LOGS_DIR"):
    LOGS_DIR = Path(os.environ["CIRUGIAS_LOGS_DIR"])
else:
    LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Cirugias Local Connector", version="0.1.0")

# CORS amplio: acepta cualquier origen incluyendo https -> http (mixed content local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


# Responder OPTIONS manualmente para garantizar que el preflight siempre pase
@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "3600",
        },
    )


manager = JobManager(logs_dir=LOGS_DIR)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "cirugias-local-connector"}


@app.post("/jobs/recetas", response_model=JobCreateResponse)
def create_recetas_job(payload: RecetasPayload) -> JobCreateResponse:
    rec = manager.create_job("recetas", payload.model_dump(by_alias=True))
    return JobCreateResponse(job_id=rec.id, status=rec.status)


@app.post("/jobs/lentess", response_model=JobCreateResponse)
def create_lentess_job(payload: LentessPayload) -> JobCreateResponse:
    rec = manager.create_job("lentess", payload.model_dump(by_alias=True))
    return JobCreateResponse(job_id=rec.id, status=rec.status)


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    rec = manager.get_job(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="job no encontrado")
    return manager.to_response(rec)

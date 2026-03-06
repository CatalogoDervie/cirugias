from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .job_manager import JobManager
from .models import JobCreateResponse, JobStatusResponse, LentessPayload, RecetasPayload

BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / "logs"

app = FastAPI(title="Cirugias Local Connector", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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

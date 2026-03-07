"""
main.py — FastAPI app del conector local
CORS manejado via middleware puro (no CORSMiddleware de FastAPI)
para compatibilidad con Chrome cuando la web es HTTPS y el conector HTTP localhost.
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .job_manager import JobManager
from .models import JobCreateResponse, JobStatusResponse, LentessPayload, RecetasPayload

if os.environ.get("CIRUGIAS_LOGS_DIR"):
    LOGS_DIR = Path(os.environ["CIRUGIAS_LOGS_DIR"])
else:
    LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Cirugias Local Connector", version="1.0.0")

_CORS = {
    "Access-Control-Allow-Origin":          "*",
    "Access-Control-Allow-Methods":         "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers":         "*",
    "Access-Control-Allow-Private-Network": "true",
    "Access-Control-Max-Age":               "86400",
}


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    """
    Inyecta CORS en todas las respuestas.
    Intercepta OPTIONS ANTES de que llegue a cualquier ruta
    (soluciona el 400 que daba CORSMiddleware con mixed-content https→http).
    Access-Control-Allow-Private-Network cubre el preflight extra de Chrome 94+.
    """
    if request.method == "OPTIONS":
        return JSONResponse(content={}, status_code=200, headers=_CORS)
    response = await call_next(request)
    for k, v in _CORS.items():
        response.headers[k] = v
    return response


manager = JobManager(logs_dir=LOGS_DIR)


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "cirugias-local-connector", "version": "1.0.0"}


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

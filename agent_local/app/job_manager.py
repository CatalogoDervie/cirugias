from __future__ import annotations

import queue
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .logging_utils import append_log
from .models import JobKind, JobStatus, JobStatusResponse, LentessPayload, RecetasPayload
from .runners.lentess_runner import run_lentess
from .runners.recetas_runner import run_recetas


@dataclass
class JobRecord:
    id: str
    kind: JobKind
    payload: Dict[str, Any]
    status: JobStatus
    created_at: datetime
    log_file: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)


class JobManager:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self._jobs: Dict[str, JobRecord] = {}
        self._queue: "queue.Queue[str]" = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def create_job(self, kind: JobKind, payload: Dict[str, Any]) -> JobRecord:
        job_id = uuid.uuid4().hex
        log_file = str(self.logs_dir / f"{job_id}.log")
        record = JobRecord(
            id=job_id,
            kind=kind,
            payload=payload,
            status="queued",
            created_at=datetime.utcnow(),
            log_file=log_file,
        )
        with self._lock:
            self._jobs[job_id] = record
        append_log(Path(log_file), f"JOB {job_id} creado ({kind})")
        self._queue.put(job_id)
        return record

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def to_response(self, record: JobRecord) -> JobStatusResponse:
        return JobStatusResponse(
            id=record.id,
            kind=record.kind,
            status=record.status,
            created_at=record.created_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
            error=record.error,
            log_file=record.log_file,
            detail=record.detail,
        )

    def _set_status(self, job_id: str, status: JobStatus, **kwargs: Any) -> None:
        with self._lock:
            rec = self._jobs[job_id]
            rec.status = status
            for k, v in kwargs.items():
                setattr(rec, k, v)

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            rec = self.get_job(job_id)
            if not rec:
                continue
            log_path = Path(rec.log_file)
            try:
                self._set_status(job_id, "running", started_at=datetime.utcnow())
                append_log(log_path, "JOB running")

                if rec.kind == "recetas":
                    payload = RecetasPayload.model_validate(rec.payload)
                    out = run_recetas(payload, log_path)
                elif rec.kind == "lentess":
                    payload = LentessPayload.model_validate(rec.payload)
                    out = run_lentess(payload, log_path)
                else:
                    raise RuntimeError(f"Tipo de job no soportado: {rec.kind}")

                self._set_status(job_id, "success", finished_at=datetime.utcnow(), detail=out)
                append_log(log_path, "JOB success")
            except Exception as exc:
                append_log(log_path, f"JOB error: {exc}")
                append_log(log_path, traceback.format_exc())
                self._set_status(
                    job_id,
                    "error",
                    finished_at=datetime.utcnow(),
                    error=str(exc),
                )
            finally:
                self._queue.task_done()

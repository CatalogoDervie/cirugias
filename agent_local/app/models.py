from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


JobKind = Literal["recetas", "lentess"]
JobStatus = Literal["queued", "running", "success", "error"]


class Credentials(BaseModel):
    user: str = Field(min_length=1)
    password: str = Field(min_length=1, alias="pass")

    model_config = {"populate_by_name": True}


class RecetasPayload(BaseModel):
    afiliado: str = Field(min_length=3)
    paciente: str = ""
    obraSocial: str = ""
    credenciales: Credentials
    diagnostico: str = Field(default="H57", min_length=1)
    medicamentos: List[List[str]] = Field(min_length=3, max_length=3)

    @field_validator("afiliado")
    @classmethod
    def _digits_afiliado(cls, value: str) -> str:
        d = "".join(ch for ch in value if ch.isdigit())
        if not d:
            raise ValueError("afiliado inválido")
        return d

    @field_validator("medicamentos")
    @classmethod
    def _valid_meds(cls, value: List[List[str]]) -> List[List[str]]:
        if len(value) != 3:
            raise ValueError("se requieren 3 pares de medicamentos")
        for pair in value:
            if len(pair) != 2 or not pair[0].strip() or not pair[1].strip():
                raise ValueError("cada receta debe tener 2 medicamentos")
        return value


class LentessPatient(BaseModel):
    afiliado: str = Field(min_length=3)
    ojo: str = Field(min_length=1)
    lio: str = Field(min_length=1)

    @field_validator("afiliado")
    @classmethod
    def _digits_afiliado(cls, value: str) -> str:
        d = "".join(ch for ch in value if ch.isdigit())
        if not d:
            raise ValueError("afiliado inválido")
        return d


class LentessPayload(BaseModel):
    credenciales: Credentials
    pacientes: List[LentessPatient] = Field(min_length=1)


class JobCreateResponse(BaseModel):
    job_id: str
    status: JobStatus


class JobStatusResponse(BaseModel):
    id: str
    kind: JobKind
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error: Optional[str] = None
    log_file: str
    detail: Dict[str, Any] = Field(default_factory=dict)

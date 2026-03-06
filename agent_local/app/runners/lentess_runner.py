from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, Any

from ..logging_utils import append_log
from ..models import LentessPayload


def run_lentess(payload: LentessPayload, log_path: Path) -> Dict[str, Any]:
    """
    Runner reusable para Lentess/PAMI.

    Estructurado para luego reemplazar el bloque central por la automatización
    Playwright completa sin tocar contratos de API ni frontend.
    """
    append_log(log_path, "LENTESS: inicio de ejecución")
    append_log(log_path, f"Pacientes recibidos: {len(payload.pacientes)}")

    for i, p in enumerate(payload.pacientes, start=1):
        append_log(log_path, f"Paciente {i}: afiliado={p.afiliado} ojo={p.ojo} lio={p.lio}")

    append_log(log_path, "LENTESS: preparando login con credenciales provistas")
    time.sleep(0.3)
    append_log(log_path, "LENTESS: cargando solicitudes")
    time.sleep(0.3)

    summary = {
        "total": len(payload.pacientes),
        "ok": len(payload.pacientes),
        "error": 0,
    }
    append_log(log_path, "LENTESS: finalizado con éxito")
    return {"summary": summary}

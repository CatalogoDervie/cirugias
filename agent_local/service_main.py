"""
Punto de entrada para el servicio empaquetado con PyInstaller.
Corre uvicorn de forma programática — sin abrir ventana de CMD.
"""
from __future__ import annotations

import sys
import os
import logging
from pathlib import Path

# Cuando PyInstaller empaqueta, los archivos quedan junto al .exe
if getattr(sys, "frozen", False):
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path(__file__).resolve().parent

# Asegurar que agent_local/ esté en el path
sys.path.insert(0, str(base_dir))

# Logs dir junto al exe
logs_dir = base_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("CIRUGIAS_LOGS_DIR", str(logs_dir))

# Cuando corre como .exe --noconsole, stdout y stderr son None.
# Uvicorn falla si intenta escribir en un stream None.
# Los redirigimos a un archivo de log antes de importar uvicorn.
log_file = logs_dir / "service.log"

if sys.stdout is None:
    sys.stdout = open(str(log_file), "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(str(log_file), "a", encoding="utf-8", buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    handlers=[logging.FileHandler(str(log_file), encoding="utf-8")],
)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
        log_config=None,   # usa nuestro basicConfig, no el formatter de colores de uvicorn
    )

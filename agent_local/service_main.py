"""
Punto de entrada para el servicio empaquetado con PyInstaller.
Corre uvicorn de forma programática — sin abrir ventana de CMD.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Cuando PyInstaller empaqueta, los archivos quedan en _MEIPASS.
# Necesitamos que el import de `app` funcione igual.
if getattr(sys, "frozen", False):
    # Corriendo como .exe
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path(__file__).resolve().parent

# Asegurar que agent_local/ esté en el path para que `from app.xxx` funcione
sys.path.insert(0, str(base_dir))

# Logs dir junto al exe
os.environ.setdefault("CIRUGIAS_LOGS_DIR", str(base_dir / "logs"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        # Sin reload — el servicio es estable
        reload=False,
    )

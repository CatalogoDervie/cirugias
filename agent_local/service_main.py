"""
service_main.py

Punto de entrada del conector. Funciona en dos modos:

  A) python service_main.py       → desarrollo, logs en consola
  B) cirugias_connector.exe       → producción, ventana mínima + logs en archivo
  C) cirugias_connector.exe --install-browser  → descarga Chrome de Playwright
"""
from __future__ import annotations

import sys
import os
import logging
import threading
from pathlib import Path

# ── Rutas ────────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    base_dir = Path(sys.executable).parent
else:
    base_dir = Path(__file__).resolve().parent

sys.path.insert(0, str(base_dir))

logs_dir = base_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("CIRUGIAS_LOGS_DIR", str(logs_dir))

log_file = logs_dir / "service.log"

# Redirigir antes de importar uvicorn (crítico cuando corre como .exe --windowed)
if sys.stdout is None:
    sys.stdout = open(str(log_file), "a", encoding="utf-8", buffering=1)
if sys.stderr is None:
    sys.stderr = open(str(log_file), "a", encoding="utf-8", buffering=1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
    handlers=[logging.FileHandler(str(log_file), encoding="utf-8")],
)


# ── Modo instalación ──────────────────────────────────────────────────────────
def _install_browser():
    """Descarga el Chrome de Playwright. Se llama con --install-browser."""
    try:
        from playwright.sync_api import sync_playwright  # noqa — solo verificar import
        import subprocess
        subprocess.run([sys.executable, "-m", "playwright", "install", "chrome"], check=True)
        # Marcar como instalado
        marker = base_dir / ".pw_ready"
        marker.write_text("ok")
    except Exception as exc:
        logging.error(f"No se pudo instalar el browser: {exc}")


# ── Servidor ──────────────────────────────────────────────────────────────────
def _run_server():
    import uvicorn
    logging.info("Conector arrancando en http://127.0.0.1:8765")
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8765,
            reload=False,
            log_config=None,
        )
    except OSError as exc:
        logging.error(f"No se pudo iniciar el servidor: {exc}")
        if "address already in use" in str(exc).lower() or "10048" in str(exc):
            _show_error_window("El puerto 8765 ya está en uso.\n\nEl conector probablemente ya está corriendo.\nCerrá la otra ventana y volvé a abrir.")
        else:
            _show_error_window(f"Error al iniciar el servidor:\n{exc}")


def _show_error_window(msg: str):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Conector Cirugías — Error", msg)
        root.destroy()
    except Exception:
        pass


# ── Ventana principal (exe mode) ──────────────────────────────────────────────
def _run_gui():
    """Ventana mínima para que el usuario sepa que el conector está activo."""
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.title("Conector Cirugías")
        root.geometry("380x200")
        root.resizable(False, False)
        root.configure(bg="#f0fdf4")

        # Centrar en pantalla
        root.update_idletasks()
        x = (root.winfo_screenwidth()  - 380) // 2
        y = (root.winfo_screenheight() - 200) // 2
        root.geometry(f"380x200+{x}+{y}")

        # Ícono de la barra de tareas (si hay .ico disponible)
        ico = base_dir / "icon.ico"
        if ico.exists():
            try:
                root.iconbitmap(str(ico))
            except Exception:
                pass

        frame = tk.Frame(root, bg="#f0fdf4", padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame, text="🟢  Conector activo",
            font=("Segoe UI", 15, "bold"),
            bg="#f0fdf4", fg="#14532d",
        ).pack(pady=(0, 4))

        tk.Label(
            frame, text="http://127.0.0.1:8765",
            font=("Courier New", 10),
            bg="#f0fdf4", fg="#374151",
        ).pack()

        tk.Label(
            frame,
            text="No cierres esta ventana mientras\nusás Recetas o Lentess desde la web.",
            font=("Segoe UI", 9),
            bg="#f0fdf4", fg="#6b7280",
            justify="center",
        ).pack(pady=(12, 16))

        def _stop():
            if messagebox.askyesno(
                "Cerrar conector",
                "¿Querés detener el conector?\n\n"
                "Recetas y Lentess dejarán de funcionar hasta que lo vuelvas a abrir."
            ):
                logging.info("Conector detenido por el usuario")
                root.destroy()
                os._exit(0)

        tk.Button(
            frame, text="Detener y cerrar",
            command=_stop,
            bg="#dc2626", fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat", padx=16, pady=7,
            cursor="hand2", bd=0,
            activebackground="#b91c1c",
            activeforeground="white",
        ).pack()

        root.protocol("WM_DELETE_WINDOW", _stop)
        root.mainloop()

    except Exception:
        # tkinter no disponible: bloqueamos el hilo principal sin hacer nada
        import time
        while True:
            time.sleep(30)


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = sys.argv[1:]

    if "--install-browser" in args:
        _install_browser()
        sys.exit(0)

    if getattr(sys, "frozen", False):
        # .exe: servidor en hilo de fondo, GUI en hilo principal
        t = threading.Thread(target=_run_server, daemon=True)
        t.start()
        # Esperar a que el servidor esté listo (máx 10s)
        import time, urllib.request
        for _ in range(50):
            try:
                urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=1)
                break
            except Exception:
                time.sleep(0.2)
        _run_gui()
    else:
        # Python directo: servidor en foreground
        logging.getLogger().addHandler(logging.StreamHandler(sys.__stdout__ or sys.stdout))
        _run_server()

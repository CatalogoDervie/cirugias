# Conector local (Windows) — Control de Cirugías

Este servicio expone endpoints en `127.0.0.1:8765` para que el frontend (`index.html`) ejecute automatizaciones sin que el usuario final use consola ni scripts manuales.

## Endpoints
- `GET /health`
- `POST /jobs/recetas`
- `POST /jobs/lentess`
- `GET /jobs/{job_id}`

## Estados de job
- `queued`
- `running`
- `success`
- `error`

## Logs
Cada job genera un log local en:
- `agent_local/logs/<job_id>.log`

## Arranque local (desarrollo)
1. Instalar Python 3.11+.
2. Crear y activar virtualenv.
3. Instalar dependencias:
   - `pip install -r agent_local/requirements.txt`
4. Instalar navegadores Playwright (una sola vez):
   - `python -m playwright install chrome`
5. Ejecutar:
   - `uvicorn agent_local.app.main:app --host 127.0.0.1 --port 8765`

## Integración con frontend existente
El frontend ya consume exactamente:
- `GET /health`
- `POST /jobs/recetas`
- `POST /jobs/lentess`
- `GET /jobs/{job_id}`

El conector usa cola serial interna para evitar ejecuciones simultáneas conflictivas.

## Nota sobre runners
Esta base incluye runners modulares:
- `app/runners/recetas_runner.py`
- `app/runners/lentess_runner.py`

Están preparados para conectar/reemplazar el bloque central por Playwright completo con mínimo impacto de API.

## Preparación para empaquetado Windows
Se incluye script base:
- `scripts/windows/run_connector.bat`

Siguiente paso recomendado: empaquetar con PyInstaller o NSSM/Task Scheduler para inicio automático.

## Verificación de ejecución real
Si un job marca `success`, en el log debe verse secuencia real (login, paciente, guardado).
Si Playwright/login/OTP falla, el estado del job será `error` (sin success falso).

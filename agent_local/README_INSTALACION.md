# Conector Local — Guía completa

---

## Para el CLIENTE

El cliente **no necesita Python ni ningún programa adicional**.
Recibe un ZIP que contiene todo incluido.

### Lo que ve el cliente:

```
ConectorCirugias_CLIENTE.zip
  ├── INSTALAR.bat          ← ejecutar solo la primera vez
  ├── Iniciar Conector.bat  ← ejecutar todos los días
  ├── LEEME.txt
  ├── python\               ← Python portátil incluido (no toca el sistema)
  └── app\                  ← código del conector
```

### Pasos para el cliente:

1. Descomprimir el zip en cualquier carpeta (ej: `C:\Conector\`)
2. Doble clic en **`INSTALAR.bat`** — esperar ~5 minutos (necesita internet)
3. Aparece ícono **"Iniciar Conector"** en el Escritorio
4. Todos los días: doble clic en ese ícono, dejar la ventana abierta

---

## Para el DESARROLLADOR (vos)

### Generar el zip para el cliente

1. Abrí `agent_local\scripts\windows\GENERAR_ZIP_CLIENTE.bat`
2. Esperá ~3-5 minutos (descarga Python embebido ~15 MB)
3. Se genera: `scripts\windows\ConectorCirugias_CLIENTE.zip`
4. Ese zip se lo mandás al cliente

El script descarga automáticamente **Python 3.12 embebido** (versión portátil
que no requiere instalación) y lo incluye dentro del zip.

### Probar el conector localmente (desarrollo)

```cmd
cd agent_local
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py -m playwright install chrome
python service_main.py
```

Servidor en http://127.0.0.1:8765

---

## Cómo funciona el Python embebido

Python embebido (`python-3.12.x-embed-amd64.zip`) es una distribución oficial
de Python.org que:
- No modifica el registro de Windows
- No requiere permisos de administrador
- Pesa ~15 MB
- Viene incluido en el zip del cliente

El `INSTALAR.bat` descarga pip y las dependencias dentro de esa carpeta Python
portátil. Todo queda autocontenido.

---

## Estructura del repositorio

```
agent_local/
├── service_main.py              ← entry point del servidor
├── requirements.txt
├── app/
│   ├── main.py                  ← FastAPI + CORS robusto
│   ├── job_manager.py           ← cola de jobs
│   ├── models.py
│   ├── logging_utils.py
│   └── runners/
│       ├── recetas_runner.py    ← automatización PAMI Recetas
│       └── lentess_runner.py    ← automatización PAMI Lentess
└── scripts/windows/
    ├── GENERAR_ZIP_CLIENTE.bat  ← genera el zip para entregar
    ├── build.bat                ← compila exe (alternativa)
    └── para_cliente_src/        ← archivos fuente del paquete cliente
        ├── INSTALAR.bat
        ├── Iniciar Conector.bat
        └── LEEME.txt
```

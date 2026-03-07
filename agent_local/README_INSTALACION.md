# Conector Local — Instalación para cliente

## ¿Qué es esto?

Un servicio de Windows que se instala **una sola vez** y corre en segundo plano.
Permite que los botones de la web ejecuten automatizaciones en PAMI sin que veas ninguna ventana de comando ni tengas que hacer nada manual.

---

## Requisitos

- Windows 10 / 11 (64 bits)
- Google Chrome instalado
- Conexión a internet

---

## Instalación (una sola vez)

### Paso 1 — Copiar archivos

Copiá la carpeta `conector\` a cualquier lugar del equipo. Por ejemplo:
```
C:\conector\
```

Debe contener:
```
conector\
  cirugias_connector.exe
  scripts\windows\
    install_service.bat
    uninstall_service.bat
    nssm.exe          ← se descarga automático si no está
  logs\               ← se crea solo
```

### Paso 2 — Instalar el servicio

1. Clic derecho sobre `install_service.bat`
2. **Ejecutar como administrador**
3. Esperar que diga `Servicio instalado y corriendo`

Eso es todo. El servicio arranca automáticamente cada vez que enciende la PC.

---

## Verificar que funciona

Abrí el navegador y entrá a:
```
http://127.0.0.1:8765/health
```
Debe responder:
```json
{"ok": true, "service": "cirugias-local-connector"}
```

O directamente usá el botón **"Conector"** en la web — si está en verde, está activo.

---

## Primera vez con PAMI (login manual único)

La **primera vez** que ejecutes Recetas PAMI o Lentess, Chrome va a abrirse **minimizado pero visible en la barra de tareas** para que puedas restaurarlo si hace falta y:
1. Hacer login con tu usuario y clave de PAMI
2. Completar captcha / OTP / código si PAMI lo pide

Después de ese login, la sesión queda guardada y todo es automático para siempre (hasta que PAMI expire la sesión, típicamente cada varios meses).

> 💡 Si ves que Chrome se abre de nuevo, es porque la sesión de PAMI venció. Solo volvé a hacer login una vez.

---

## Desinstalar

1. Clic derecho sobre `uninstall_service.bat`
2. **Ejecutar como administrador**

---

## Logs de cada automatización

Cada ejecución genera un log en:
```
conector\logs\<job_id>.log
```

Si algo falla, ahí está el detalle completo.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| El botón de la web dice "Conector: no detectado" | El servicio no está corriendo. Abrí `services.msc`, buscá `CirugiasConector` y dale Start. |
| Chrome se abre o se restaura solo | El sistema detectó login/captcha/OTP y te deja intervenir manualmente. Después sigue solo. |
| Error "Afiliado no encontrado" | Verificar el número de afiliado en el sistema. |
| Quiero reinstalar | Ejecutá `uninstall_service.bat` y luego `install_service.bat` de nuevo. |

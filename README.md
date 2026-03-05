# Cirugías - Pestaña WhatsApp

## Uso operativo (sin Excel)
## Dominio productivo
- App: `https://centrodeojos-estevesesteves.com.ar/controldecirugias/`
- Documento preparación: `https://centrodeojos-estevesesteves.com.ar/preparacion/`
- Documento consentimiento: `https://centrodeojos-estevesesteves.com.ar/consentimiento/`

1. Abrí la pestaña **💬 WhatsApp** (carga pacientes del sistema automáticamente).
2. Elegí **Fecha de cirugía (global)**. Esa fecha se usa para todos los envíos y queda guardada en `localStorage` (`wa_global_date`).
3. Si querés, activá **Solo estado: Llegó lente** para trabajar únicamente esos casos.
4. Completá/ajustá la **Hora** por paciente directamente en la tabla (se guarda en el registro principal del paciente).
5. Elegí canal: **WhatsApp Desktop** (`whatsapp://`) o **WhatsApp Web**.

## Acciones por paciente
- **📩 Confirmar turno**: valida fecha global + hora + teléfono y envía el mensaje de confirmación.
- **✅ Confirmó**: checkbox persistente por paciente (`wa_confirmed_map`).
- **📎 Enviar documentos**: se habilita solo si está confirmado; envía mensaje (incluye links directos a ambos PDFs), intenta abrir los 2 PDFs en nuevas pestañas y actualiza el registro principal a **FECHA PROGRAMADA** con la fecha global (y hora si existe).

## Teléfono override (solo WhatsApp)
- El teléfono editable del tab WhatsApp es un override local y **no modifica** el teléfono clínico principal.
- Se guarda en `localStorage` (`wa_phone_override`) y se usa en los envíos.

## Tracking y reset
- Se guarda tracking por paciente para **turno enviado** y **docs enviados** (`wa_tracking_map`).
- Botones masivos:
  - **Enviar turnos (filtrados)**
  - **Enviar docs (confirmados)**
  - **Detener**
- **Reset tracking** limpia tracking, confirmaciones y overrides para reiniciar la campaña.

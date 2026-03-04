# Cirugías - Pestaña WhatsApp

## Cómo usar la pestaña WhatsApp
1. Abrí la pestaña **💬 WhatsApp**.
2. Elegí el origen:
   - **Cargar desde sistema**: toma pacientes desde la app.
   - **Archivo Excel**: cargá `.xlsx/.xls/.csv` con columnas (Apellido, Nombre, Telefono_WhatsApp, Fecha, Hora).
3. Opcionales:
   - Activá **Solo estado: Llegó lente** para enviar solo esos casos.
   - Elegí canal: **WhatsApp Desktop** (`whatsapp://`) o **WhatsApp Web**.
   - Ajustá delay (default 4000 ms) para **Enviar todos**.
4. Podés enviar individual con **Abrir** o masivo con **Enviar todos**.

## Tracking “Enviado”
- Cada envío marca `enviadoAt` en `localStorage` por paciente/fila (tracking WhatsApp, no clínico).
- Se muestra como `✅ Enviado (dd/mm hh:mm)` en la tabla.

## Reset de enviados
- Usá **Reset enviados** en la pestaña WhatsApp para limpiar todo el tracking local y comenzar de cero.
- Al cambiar entre **Excel / sistema** o al alternar **Solo estado: Llegó lente**, también se reinician los contadores de la corrida actual (enviados/errores).

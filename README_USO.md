# Manual de uso

## Login
1. Abrir sistema.
2. Ingresar email y contraseña.
3. Sin sesión activa, el panel queda bloqueado.

## Tabla y búsqueda
- Buscar por paciente, DNI o lente.
- Filtrar por estado y ojo.
- Paginación con botones Anterior/Siguiente.

## Crear y editar
- Botón **Nuevo registro** para alta.
- Botón **Editar** por fila para modificar.
- Roles:
  - `admin`: alta/edición/borrado por regla.
  - `operador`: alta/edición.
  - `readonly`: solo lectura.

## Alertas
- Se muestran autorizaciones pendientes.
- Se muestran cirugías próximas (0 a 3 días).

## Auditoría
- Cada alta/edición guarda evento en `audit_log` con:
  - `userId`, `action`, `docId`, `timestamp`,
  - `changedFields`, `oldValues`, `newValues`.

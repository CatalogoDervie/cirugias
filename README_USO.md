# README_USO.md

## 1) Ingreso al sistema
Pantalla de acceso pide:
- **USUARIO**
- **CONTRASEÑA**

Ingreso inicial administrador:
- Usuario: `mjme`
- Contraseña inicial: `campesino123`

## 2) Cambio obligatorio de contraseña
En el primer ingreso:
1. El sistema muestra pantalla de cambio obligatorio.
2. Ingresar nueva contraseña y confirmar.
3. El sistema cierra sesión.
4. Volver a ingresar con la nueva contraseña.

## 3) Uso de la tabla principal
- Búsqueda por paciente, DNI, lente o administrativo.
- Filtro por estado.
- Filtro por ojo (OD/OI).
- Paginación con botones **Anterior** y **Siguiente**.

## 4) Gestión de registros
### Admin
- Ver, crear, editar, eliminar.
- Ver panel de administración de usuarios.
- Acceso de lectura a auditoría (por reglas).

### Operador
- Ver, crear, editar.
- No elimina.

### Readonly
- Solo lectura.

## 5) Alertas administrativas
El sistema muestra alertas por:
- Autorización pendiente.
- Cirugías próximas (0 a 3 días).

## 6) Auditoría
Cada acción de negocio relevante registra en `audit_log`:
- `userId`
- `username`
- `action`
- `docId`
- `timestamp`
- `changedFields`
- `oldValues`
- `newValues`

## 7) Backup rápido
Botón **Copiar backup (texto)**:
- Copia al portapapeles un JSON de la página actual de registros.
- No genera archivos binarios.

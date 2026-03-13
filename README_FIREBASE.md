# Configuración Firebase

## 1) Crear proyecto
- Ir a consola Firebase y crear proyecto nuevo.

## 2) Authentication
- Activar método **Email/Password**.
- Crear usuarios administrativos.

## 3) Firestore
- Crear base en modo producción.
- Cargar reglas desde `firestore.rules`.

## 4) Estructura recomendada
- Colección `users`:
  - Documento ID = `uid` del usuario.
  - Campos: `displayName`, `role` (`admin`, `operador`, `readonly`).
- Colección `surgeries`: registros administrativos de cirugía.
- Colección `audit_log`: trazabilidad de cambios.

## 5) Configuración web
- Copiar `js/config.example.js` a `js/config.js` con la configuración del proyecto.

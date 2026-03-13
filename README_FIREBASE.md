# README_FIREBASE.md

## 1) Crear proyecto Firebase
1. Ir a https://console.firebase.google.com/
2. Crear proyecto nuevo (ejemplo: `control-cirugias-esteves`).
3. Agregar app Web en Firebase y copiar configuración.

## 2) Habilitar Authentication
1. Ir a **Authentication** > **Sign-in method**.
2. Activar **Email/Password**.

## 3) Crear usuario técnico inicial en Authentication
Crear usuario técnico (no visible en UI final):
- Email técnico sugerido: `mjme.admin@interno.local`
- Contraseña inicial: `campesino123`

> Nota: el usuario final nunca ingresa email en la UI, solo `usuario`.

## 4) Crear Firestore
1. Ir a **Firestore Database**.
2. Crear base en modo producción.
3. Ir a **Rules** y pegar contenido de `firestore.rules`.
4. Publicar reglas.

## 5) Crear documento admin inicial en colección `users`
Crear colección `users` y documento con ID igual al UID del usuario Authentication creado en paso 3.
Campos obligatorios:
```json
{
  "username": "mjme",
  "username_lc": "mjme",
  "displayName": "MJME",
  "role": "admin",
  "active": true,
  "mustChangePassword": true,
  "authEmail": "mjme.admin@interno.local"
}
```

## 6) Forzar cambio de contraseña inicial
- El campo `mustChangePassword: true` dispara pantalla obligatoria de cambio en primer ingreso.
- Cuando el usuario cambia contraseña dentro de la app, se actualiza automáticamente a `false`.

## 7) Configuración del proyecto web
1. Copiar `js/config.example.js` a `js/config.js`.
2. Reemplazar credenciales:
   - `apiKey`
   - `authDomain`
   - `projectId`
   - `storageBucket`
   - `messagingSenderId`
   - `appId`
3. No subir `js/config.js` público si contiene datos sensibles del entorno interno.

## 8) Alta de futuros usuarios sin exponer mails en interfaz
Flujo seguro recomendado:
1. Admin crea usuario en Firebase Authentication (email técnico interno + contraseña temporal).
2. Admin obtiene UID del usuario en Authentication.
3. Admin carga/edita perfil interno en colección `users` (desde panel admin o manual):
   - `username` (visible para login)
   - `username_lc`
   - `displayName`
   - `role`: `admin` | `operador` | `readonly`
   - `active`
   - `mustChangePassword: true`
   - `authEmail` (técnico, no visible en UI de login)
4. Usuario final entra con `username` + contraseña temporal y cambia contraseña en primer ingreso.

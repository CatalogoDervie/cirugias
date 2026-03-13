# README_INSTALACION.md

## 1) Guardar archivos del proyecto
1. Crear una carpeta local, por ejemplo `cirugias`.
2. Copiar dentro todos los archivos y carpetas del árbol entregado.
3. Verificar que existe `js/config.example.js`.
4. Copiar `js/config.example.js` como `js/config.js`.
5. Completar `js/config.js` con credenciales reales de Firebase.

## 2) Ejecución local
Opción recomendada con servidor local:
```bash
cd cirugias
python3 -m http.server 5500
```
Abrir:
- `http://localhost:5500/index.html`
- `http://localhost:5500/importar_datos.html`

## 3) Prueba inicial
1. Cargar reglas Firestore de `firestore.rules`.
2. Configurar Authentication y colecciones siguiendo `README_FIREBASE.md`.
3. Ingresar con usuario interno:
   - Usuario: `mjme`
   - Contraseña inicial: `campesino123`
4. En primer ingreso se exige cambio obligatorio de contraseña.
5. Luego del cambio, volver a loguear con la nueva contraseña.

## 4) Confirmaciones mínimas de funcionamiento
- Sin sesión activa no se ve el panel principal.
- Con rol `readonly` no aparece edición ni eliminación.
- Con rol `operador` hay alta/edición, sin eliminación.
- Con rol `admin` hay alta/edición/eliminación y panel de usuarios.
- El importador guarda en la misma colección de negocio: `cirugias`.

# Instalación local (texto plano)

1. Clonar repositorio:
   - `git clone https://github.com/CatalogoDervie/cirugias.git`
   - `cd cirugias`
2. Crear archivo de configuración:
   - Copiar `js/config.example.js` a `js/config.js`.
   - Completar credenciales Firebase.
3. Abrir localmente:
   - Opción rápida: abrir `index.html` con un servidor estático.
   - Recomendado: `python3 -m http.server 5500` y abrir `http://localhost:5500`.
4. Probar:
   - Ingresar con un usuario creado en Firebase Authentication.
   - Verificar que sin sesión no se muestra el panel.

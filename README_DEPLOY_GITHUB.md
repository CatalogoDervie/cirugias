# README_DEPLOY_GITHUB.md

## 1) Preparar repositorio
```bash
git init
git add .
git commit -m "Control de cirugías - versión estable"
```

## 2) Subir a GitHub
```bash
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git branch -M main
git push -u origin main
```

## 3) Activar GitHub Pages
1. Ir al repositorio en GitHub.
2. Entrar en **Settings** > **Pages**.
3. Source: **Deploy from a branch**.
4. Branch: `main`, carpeta `/ (root)`.
5. Guardar y esperar URL pública.

## 4) Publicar cambios futuros
```bash
git add .
git commit -m "Actualización"
git push
```

## 5) Checklist antes de publicar
- `js/config.js` completo y correcto.
- Reglas Firestore publicadas.
- Usuario admin inicial creado en Authentication y `users`.
- Prueba login por username (`mjme`) funcionando.

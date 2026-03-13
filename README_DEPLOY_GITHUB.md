# Deploy en GitHub Pages

1. Confirmar que `js/config.js` apunta al proyecto Firebase correcto.
2. Subir cambios:
   - `git add .`
   - `git commit -m "Deploy control de cirugías"`
   - `git push origin <rama>`
3. En GitHub > Settings > Pages:
   - Source: Deploy from a branch.
   - Branch: `main` (o la rama de publicación), carpeta `/root`.
4. Esperar publicación y validar URL pública.
5. En cada actualización: commit + push.

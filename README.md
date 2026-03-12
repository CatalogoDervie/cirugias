# Control de Cirugías — Centro de Ojos Esteves v3

## Estructura final del proyecto

```
/  (raíz — GitHub Pages)
├── index.html               ← App principal ✅ RECONSTRUIDA
├── firebase.js              ← Conector Firestore ✅ RECONSTRUIDO
├── importar_datos.html      ← Importador masivo ✅ NUEVO
├── datos_desde_excel.json   ← Tus 107 registros del Excel ✅ LISTO
├── CNAME                    ← centrodeojos-estevesesteves.com.ar
├── preparacion/index.html   ← Módulo preparación quirúrgica
├── consentimiento/index.html← Módulo consentimiento
├── CONSENTIMIENTO CX 2026.pdf
└── PREPARACIN PARA LA CIRUGIA.pdf
```

## Archivos a ELIMINAR del repo actual

- `agent_local/` → carpeta completa (backend Python, no va a GitHub Pages)
- `importar_firestore.html` → reemplazado por `importar_datos.html`
- `cirugias_firestore_import.json` → reemplazado por `datos_desde_excel.json`
- `controldecirugias.html` → redirect innecesario
- `controldecirugias/index.html` → idem
- `404.html` → opcional

## Pasos para poner en marcha

### 1. Reemplazar archivos
Copiá `index.html`, `firebase.js`, `importar_datos.html` y `datos_desde_excel.json`
en la raíz del repositorio.

### 2. Subir a GitHub
```bash
git add -A
git commit -m "v3: sistema reconstruido + datos Excel importados"
git push
```

### 3. Importar los datos del Excel a Firestore
1. Abrí `importar_datos.html` en el navegador
2. Hacé click en **"🔍 Ver cuántos registros hay"** para verificar estado actual
3. Cargá el archivo `datos_desde_excel.json` con el selector de archivo
4. Hacé click en **"📤 Importar JSON a Firestore"**
5. Esperá que el log diga **✅ Listo**

### 4. Verificar
- Abrí `index.html`
- Deberías ver ✓ Firestore en línea (esquina superior derecha)
- Los 107 registros del Excel deben aparecer en la tabla

## Reglas de Firestore (pegar en Firebase Console → Reglas)

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /cirugias/{docId} {
      allow read, write: if true;
    }
  }
}
```

## Columnas del sistema (nuevas vs antiguo)

| Campo nuevo | Antes | Fuente Excel |
|-------------|-------|--------------|
| `lio`       | `dioptria` | Aumento Lente (LIO) |
| `autorizacion` | ❌ no existía | Autorización |
| `mejoraLente` | ❌ no existía | Mejora de lente |
| `estadoLente` | parcial | Estado de la Lente |

## Bugs corregidos vs versión anterior

1. **Edición de pacientes no funcionaba** → IDs string vs número (fix crítico)
2. **Firebase condición de carrera** → sistema de espera con evento `firestoreReady`
3. **Columnas faltantes** → autorizacion, mejoraLente, estadoLente agregadas
4. **Alertas mejoradas** → falta autorización, cirugía próxima sin lente, segundo ojo
5. **Panel de alertas independiente** → tab dedicado con tabla completa

## Plan gratuito Firebase (Spark)

- 50.000 lecturas / día
- 20.000 escrituras / día
- 1 GB almacenamiento

Para 2 clínicas con uso normal (< 500 escrituras/día) → suficiente.

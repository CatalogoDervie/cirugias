# Auditoría técnica integral — Sistema de Cirugías (Centro de Ojos Esteves)

Fecha: 2026-03-13  
Alcance auditado: repositorio estático (`index.html`, `firebase.js`, `importar_datos.html`, `README.md`) y despliegue objetivo en GitHub Pages + Firebase.

---

## Resumen ejecutivo

El sistema muestra una evolución funcional sólida para operación administrativa diaria, pero **no cumple actualmente con un nivel de seguridad esperado para un sistema médico** por su arquitectura 100% cliente, reglas Firestore abiertas, falta de autenticación robusta y ausencia de trazabilidad inviolable de cambios.

La app puede seguir operando en el corto plazo con mitigaciones rápidas (hardening de reglas, Auth, eliminación de credenciales en `localStorage`, backups externos). Para una clínica real y crecimiento a 50k+ registros, se recomienda migrar a arquitectura híbrida (frontend + capa backend mínima con Cloud Functions) y gobierno de datos formal.

---

## 1) Lista completa de problemas encontrados

> Escala de gravedad: **Alto / Medio / Bajo**.

### Arquitectura del sistema

1. **Arquitectura de escritura directa desde navegador a Firestore (sin capa de dominio/servidor)**  
   - Gravedad: **Alto**  
   - Riesgo: cualquier cliente con acceso puede intentar operaciones directas; difícil imponer reglas de negocio complejas, validaciones fuertes y auditoría regulatoria.  
   - Evidencia: el frontend usa `window.firestoreConnector` con `upsertRow/deleteRow/listenRows` y maneja estado primario en cliente.

2. **Lógica de negocio crítica concentrada en un único `index.html` monolítico**  
   - Gravedad: **Medio**  
   - Riesgo: alto acoplamiento, deuda técnica, mayor probabilidad de regresiones y baja mantenibilidad.

3. **Dependencia de `localStorage`/IndexedDB como capa operativa principal de fallback**  
   - Gravedad: **Medio**  
   - Riesgo: inconsistencias entre pestañas/equipos, sobrescrituras, falta de garantías transaccionales.

### Seguridad

4. **Reglas Firestore documentadas como públicas (`allow read, write: if true`)**  
   - Gravedad: **Alto**  
   - Riesgo: lectura/escritura sin restricción; exposición total de datos clínico-administrativos.

5. **Sin autenticación/autorización de usuarios en app principal**  
   - Gravedad: **Alto**  
   - Riesgo: no existe control de identidad ni perfiles (admin, facturación, coordinación quirúrgica).

6. **Credenciales de integraciones guardadas en `localStorage`**  
   - Gravedad: **Alto**  
   - Riesgo: robo por XSS, acceso físico/equipo compartido, exfiltración de usuario/clave.

7. **Importador con función de borrado total (`limpiarFirestore`) accesible desde HTML cliente**  
   - Gravedad: **Alto**  
   - Riesgo: borrado masivo accidental o malicioso.

8. **Sin rastro de CSP/HSTS/headers de endurecimiento en despliegue estático**  
   - Gravedad: **Medio**  
   - Riesgo: mayor superficie frente a inyección y ataques de navegador.

### Confiabilidad de datos

9. **Cola offline persistida en `localStorage` sin integridad criptográfica ni versionado**  
   - Gravedad: **Medio**  
   - Riesgo: manipulación local, replay, pérdida silenciosa si storage se limpia.

10. **Generación de IDs por `Date.now()` en camino de guardado**  
    - Gravedad: **Medio**  
    - Riesgo: colisiones bajo concurrencia o multiusuario, dificultad para trazabilidad consistente.

11. **Backups locales de corta retención (3 días) y sin estrategia externa automática**  
    - Gravedad: **Medio**  
    - Riesgo: recuperación limitada ante incidente tardío/ransomware/error humano.

12. **Sin bitácora inmutable de cambios (quién cambió qué y cuándo, con razón del cambio)**  
    - Gravedad: **Alto**  
    - Riesgo: incumplimiento operativo y legal en entornos sanitarios.

### Performance

13. **Carga potencialmente completa de colección en cliente (`getDocs`/`onSnapshot` sobre colección)**  
    - Gravedad: **Medio**  
    - Riesgo: degradación al crecer volumen (50k registros), mayor costo de lecturas Firestore.

14. **Archivo único grande con UI + reglas + procesos; impacto en parse/TTI**  
    - Gravedad: **Medio**  
    - Riesgo: inicio más lento en equipos administrativos modestos.

15. **Sin estrategia explícita de paginado/virtualización server-driven**  
    - Gravedad: **Medio**  
    - Riesgo: tabla pesada, filtros menos eficientes, consumo de memoria creciente.

### UX para administrativos

16. **Alta densidad de funciones en una sola vista puede inducir error operativo**  
    - Gravedad: **Medio**  
    - Riesgo: acciones críticas (editar/borrar/importar) sin barreras contextuales suficientes.

17. **Mensajería de estado técnica para usuarios no técnicos**  
    - Gravedad: **Bajo**  
    - Riesgo: confusión sobre “cola offline”, “listener”, “reconectando”.

18. **No se observa circuito formal de doble confirmación para operaciones destructivas globales**  
    - Gravedad: **Medio**  
    - Riesgo: errores humanos en tareas masivas.

### Escalabilidad futura

19. **Modelo sin partición por clínica/sede y sin namespace de tenant robusto**  
    - Gravedad: **Alto**  
    - Riesgo: crecimiento desordenado, controles de acceso difíciles y consultas costosas.

20. **Sin esquema de índices y consultas orientadas a volumen (fecha/estado/obra social/sede)**  
    - Gravedad: **Medio**  
    - Riesgo: latencia y costos crecientes a medida que aumentan registros.

---

## 2) Propuestas de solución concreta (por problema)

1) **Mover escritura crítica a backend controlado** (Cloud Functions HTTPS + callable).  
2) **Modularizar frontend** (dominio, UI, data-access, integraciones).  
3) **Reducir dependencia de storage local** a caché no-canónica + reconciliación con versionado de documento.  
4) **Cerrar reglas Firestore** con `request.auth != null` y validaciones por rol/sede/campos.  
5) **Implementar Firebase Auth** (email/password + MFA opcional) y claims por rol (`admin`, `coordinacion`, `facturacion`, `solo_lectura`).  
6) **Eliminar credenciales de `localStorage`**; usar token efímero emitido por backend y vault seguro del lado servidor.  
7) **Restringir import/borrado masivo** a rol administrador + pantalla separada + doble factor + “type-to-confirm”.  
8) **Agregar headers de seguridad** vía Cloudflare/Vercel proxy o Firebase Hosting (si migran): CSP, HSTS, X-Frame-Options, Referrer-Policy.  
9) **Firmar y versionar operaciones offline** con `opId`, `actorId`, `deviceId`, `baseVersion`; resolver conflictos por estrategia definida.  
10) **Usar IDs robustos** (`doc().id`/UUIDv7) y timestamps de servidor como fuente de verdad.  
11) **Backups automáticos externos** (Firestore export diario a GCS + retención 30/90/365 + prueba de restore mensual).  
12) **Crear auditoría de cambios** en colección append-only (`audit_logs`) con hash de encadenamiento.  
13) **Paginado y consultas indexadas** (`limit`, `startAfter`, filtros por estado/sede/fecha).  
14) **Code splitting/lazy loading** para módulos pesados (WhatsApp, reportes, importación).  
15) **Virtualización de tabla** y memoización de filtros.  
16) **UX de seguridad operacional**: separar “edición diaria” de “operaciones peligrosas”.  
17) **Mensajes funcionales** (“Guardado”, “Pendiente de sincronización”) y ayuda contextual simple.  
18) **Flujo de aprobación** para borrados/ediciones sensibles (2 pasos + motivo obligatorio).  
19) **Modelo multi-sede**: `clinics/{clinicId}/surgeries/{id}` + claims por sede.  
20) **Plan de índices y ciclo de vida de datos** (archivo histórico, partición temporal lógica).

---

## 3) Evaluación por las 6 dimensiones solicitadas

### 1. Arquitectura
- Adecuada para MVP administrativo de bajo riesgo.  
- **No adecuada** en su forma actual para entorno médico con exigencias de seguridad/auditoría y crecimiento.

### 2. Seguridad
- Principal brecha: reglas públicas + falta de autenticación/roles + secretos locales.  
- Requiere remediación inmediata antes de ampliar usuarios/sedes.

### 3. Confiabilidad de datos
- Buen enfoque offline-first operativo, pero sin controles robustos de integridad, conflicto y trazabilidad.  
- Riesgo medio/alto ante incidentes de sincronización o borrados.

### 4. Performance
- Correcta para volumen actual moderado, pero insuficiente para 50k si continúa el patrón de carga completa en cliente.

### 5. UX administrativo
- Funcionalmente rica; riesgo de sobrecarga cognitiva y errores en acciones críticas.  
- Recomendable simplificar flujos y reforzar validaciones humanas.

### 6. Escalabilidad
- Necesita rediseño de modelo de datos, acceso y consultas para crecer sin disparar costo/latencia.

---

## 4) Plan de rearquitectura del sistema

### Fase 0 (0–2 semanas) — Contención inmediata
- Cerrar reglas Firestore y habilitar Auth.  
- Despublicar importador/borrado masivo en producción.  
- Eliminar persistencia de credenciales en navegador.  
- Backup diario automático + checklist manual semanal.

### Fase 1 (2–6 semanas) — Base robusta
- Introducir capa backend mínima (Cloud Functions).  
- Endpoint de operaciones críticas: alta/edición/baja con validación de esquema.  
- Implementar `audit_logs` append-only.  
- Refactor frontend por módulos.

### Fase 2 (6–10 semanas) — Escalabilidad y operación clínica
- Multi-sede y RBAC fino por claims.  
- Paginado/índices, vistas filtradas por rol.  
- Alertas administrativas por motor de reglas (Cloud Scheduler + Functions).  
- Tablero de salud operativa (errores sync, pendientes, lecturas/escrituras).

### Fase 3 (10–14 semanas) — Gobierno y cumplimiento
- Política de retención y archivado histórico.  
- Pruebas de restauración periódicas.  
- Procedimientos de incidente y continuidad operativa.  
- Capacitación a administrativos + manual SOP.

---

## 5) Estructura de archivos recomendada

```text
/ (frontend)
  /src
    /app
      main.js
      router.js
    /modules
      /pacientes
      /cirugias
      /lentes
      /autorizaciones
      /reportes
    /shared
      /ui
      /utils
      /validation
    /services
      auth.service.js
      surgeries.service.js
      audit.service.js
      cache.service.js
    /state
      store.js
      selectors.js
    /styles
  index.html

/functions (backend)
  /src
    auth/
    surgeries/
    lenses/
    audits/
    alerts/
    backups/
  package.json

/firebase
  firestore.rules
  firestore.indexes.json
  storage.rules

/docs
  arquitectura.md
  modelo_datos.md
  runbooks/
```

---

## 6) Mejoras específicas solicitadas

### Mejoras de Firebase
- Auth + custom claims + reglas por colección y campos.  
- Subcolecciones por clínica/sede.  
- Índices compuestos para filtros operativos.

### Control de usuarios
- Roles: `admin`, `coordinacion`, `facturacion`, `consulta`.  
- Sesión con expiración y reautenticación para acciones críticas.

### Manejo de caché
- Caché solo para lectura rápida; escritura validada por backend.  
- Política de invalidación por versión (`rowVersion`).

### Sistema de alertas administrativas
- Alertas en tiempo real + digest diario por email/WhatsApp empresarial.  
- Severidad y SLA por tipo (lente demorado, cirugía sin autorización, etc.).

### Estrategia de backup
- Export automático diario Firestore→GCS, retención escalonada.  
- Restore test mensual documentado.

### Mejoras de rendimiento
- Paginado server-driven, virtualización de tabla, lazy loading de módulos.  
- Métricas: TTI, errores JS, latencia de consultas, costo Firestore por usuario.

---

## 7) Roadmap de impacto esperado

- **Seguridad**: reducción drástica del riesgo de acceso no autorizado y borrado masivo.  
- **Confiabilidad**: mejor trazabilidad y recuperación ante incidentes.  
- **Operación**: UX más segura para administrativos con menor probabilidad de error.  
- **Escalabilidad**: camino claro hacia 50k+ registros con costos controlados.


// firebase.js — Firestore connector v4 — Control de Cirugías
// Arquitectura: offline-first con cola de escritura persistente + reconexión automática
// Compatible con GitHub Pages | ES modules nativos | Sin bundler

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import {
  getFirestore,
  enableIndexedDbPersistence,
  collection, doc, setDoc, getDocs,
  deleteDoc, onSnapshot, serverTimestamp
} from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js';

const firebaseConfig = {
  apiKey: 'AIzaSyDf49KWGdZp1C3t42LSopS_VuNiaabFZQw',
  authDomain: 'control-cirugias-c9c71.firebaseapp.com',
  projectId: 'control-cirugias-c9c71',
  storageBucket: 'control-cirugias-c9c71.firebasestorage.app',
  messagingSenderId: '714322418539',
  appId: '1:714322418539:web:523a8e5ad295d277b20a2e'
};

// ══════════════════════════════════════════════════════════════
// COLA DE ESCRITURA OFFLINE — persiste en localStorage
// Si no hay red, los cambios se encolan y se envían al reconectar
// ══════════════════════════════════════════════════════════════
const QUEUE_KEY = 'fsc_write_queue';
function queueLoad() { try { return JSON.parse(localStorage.getItem(QUEUE_KEY) || '[]'); } catch { return []; } }
function queueSave(q) { try { localStorage.setItem(QUEUE_KEY, JSON.stringify(q)); } catch(e) { console.warn('[Queue] no se pudo persistir:', e.message); } }
function queueAdd(op) {
  const q = queueLoad();
  if (op.type === 'upsert') {
    const idx = q.findIndex(x => x.type === 'upsert' && String(x.row.id) === String(op.row.id));
    if (idx !== -1) { q[idx] = op; queueSave(q); return; }
  }
  q.push(op); queueSave(q);
}

// ══════════════════════════════════════════════════════════════
// INIT FIREBASE
// ══════════════════════════════════════════════════════════════
let readyResolve;
const readyPromise = new Promise(r => { readyResolve = r; });
let app, db, cirugiasRef, _initOk = false;

(async () => {
  try {
    app = initializeApp(firebaseConfig);
    db = getFirestore(app);
    try {
      await enableIndexedDbPersistence(db, { synchronizeTabs: true });
    } catch(e) {
      if (e.code !== 'failed-precondition' && e.code !== 'unimplemented') {
        console.warn('[Firebase] persistencia:', e.code, e.message);
      }
    }
    cirugiasRef = collection(db, 'cirugias');
    _initOk = true;
    readyResolve(true);
  } catch(e) {
    console.error('[Firebase] init error:', e);
    readyResolve(false);
  }
})();

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════
function normVal(v) {
  if (v && typeof v.toDate === 'function') return v.toDate().toISOString().slice(0, 10);
  return v;
}
function normRow(raw, docId) {
  const row = {};
  for (const [k, v] of Object.entries(raw || {})) row[k] = normVal(v);
  row.id = String(row.id ?? docId ?? '');
  return row;
}
function sanitize(row) {
  const out = { ...row };
  const now = new Date().toISOString();
  out.id = String(out.id || '');
  if (!out.createdAt) out.createdAt = now;
  out.updatedAt = now;
  for (const k of Object.keys(out)) { if (out[k] === undefined) out[k] = null; }
  return out;
}
async function withRetry(fn, retries = 4, baseMs = 500) {
  let lastErr;
  for (let i = 1; i <= retries; i++) {
    try { return await fn(); } catch (e) {
      lastErr = e;
      if (i < retries) {
        const delay = baseMs * Math.pow(2, i - 1);
        console.warn(`[Firestore] intento ${i}/${retries} → esperando ${delay}ms`, e.message);
        await new Promise(r => setTimeout(r, delay));
      }
    }
  }
  throw lastErr;
}

// ══════════════════════════════════════════════════════════════
// FLUSH DE COLA — envía operaciones pendientes a Firestore
// ══════════════════════════════════════════════════════════════
let _flushRunning = false;
async function flushQueue() {
  if (_flushRunning || !_initOk) return;
  const q = queueLoad();
  if (!q.length) return;
  _flushRunning = true;
  console.log(`[Queue] flushing ${q.length} ops pendientes...`);
  const remaining = [...q];
  for (const op of q) {
    try {
      if (op.type === 'upsert') {
        const s = sanitize(op.row);
        await withRetry(() => setDoc(doc(cirugiasRef, s.id), { ...s, _srv: serverTimestamp() }, { merge: true }));
      } else if (op.type === 'delete') {
        await withRetry(() => deleteDoc(doc(cirugiasRef, String(op.id))));
      }
      const idx = remaining.findIndex(x => x._qid === op._qid);
      if (idx !== -1) remaining.splice(idx, 1);
      queueSave(remaining);
    } catch (e) { console.error(`[Queue] op falló permanentemente:`, e.message); }
  }
  _flushRunning = false;
  const left = queueLoad().length;
  if (left > 0) console.warn(`[Queue] ${left} ops siguen pendientes`);
  else { console.log('[Queue] vacía ✓'); window.dispatchEvent(new CustomEvent('firestoreQueueFlushed')); }
}

// Flush automático al recuperar red
window.addEventListener('online', () => { console.log('[Firebase] red recuperada → flush...'); setTimeout(flushQueue, 1500); });

// ══════════════════════════════════════════════════════════════
// API PÚBLICA
// ══════════════════════════════════════════════════════════════
async function upsertRow(row) {
  const s = sanitize(row);
  const id = String(s.id || Date.now());
  s.id = id;
  const qid = `upsert_${id}_${Date.now()}`;
  queueAdd({ _qid: qid, type: 'upsert', row: s, ts: new Date().toISOString() });
  if (!_initOk) { console.warn('[Firestore] no inicializado, op en cola'); return id; }
  try {
    await withRetry(() => setDoc(doc(cirugiasRef, id), { ...s, _srv: serverTimestamp() }, { merge: true }));
    const q = queueLoad().filter(x => x._qid !== qid); queueSave(q);
  } catch (e) {
    console.warn('[Firestore] upsert encolado (offline?):', e.message);
    throw e;
  }
  return id;
}

async function deleteRow(id) {
  const sid = String(id);
  const qid = `del_${sid}_${Date.now()}`;
  queueAdd({ _qid: qid, type: 'delete', id: sid, ts: new Date().toISOString() });
  if (!_initOk) { console.warn('[Firestore] no inicializado, delete en cola'); return; }
  try {
    await withRetry(() => deleteDoc(doc(cirugiasRef, sid)));
    const q = queueLoad().filter(x => x._qid !== qid); queueSave(q);
  } catch (e) { console.warn('[Firestore] delete encolado:', e.message); throw e; }
}

async function replaceAllRows(rows = []) {
  const CHUNK = 20;
  for (let i = 0; i < rows.length; i += CHUNK) {
    await Promise.all(rows.slice(i, i + CHUNK).map(r => upsertRow(r)));
  }
}

function listenRows(onRows, onErr) {
  if (!_initOk) { console.warn('[Firestore] listenRows sin init'); return () => {}; }
  return onSnapshot(
    cirugiasRef,
    { includeMetadataChanges: false },
    snap => onRows(snap.docs.map(d => normRow(d.data(), d.id))),
    onErr || (e => console.error('[Firestore] listener:', e))
  );
}

async function exportAllRows() {
  if (!_initOk) throw new Error('Firestore no inicializado');
  const snap = await getDocs(cirugiasRef);
  return snap.docs.map(d => normRow(d.data(), d.id));
}

function pendingCount() { return queueLoad().length; }
async function forcSync() { await flushQueue(); }

// ══════════════════════════════════════════════════════════════
// EXPONER
// ══════════════════════════════════════════════════════════════
window.firestoreConnector = { ready: readyPromise, upsertRow, replaceAllRows, deleteRow, listenRows, exportAllRows, pendingCount, forcSync, flushQueue };

readyPromise.then(ok => {
  window.dispatchEvent(new CustomEvent('firestoreReady', { detail: { ok } }));
  if (ok) setTimeout(flushQueue, 2000);
});

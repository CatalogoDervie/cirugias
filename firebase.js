// firebase.js — Firestore connector para Control de Cirugías
// Compatible con GitHub Pages (sin bundler, ES modules nativos)

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import {
  getFirestore,
  collection,
  doc,
  setDoc,
  getDocs,
  deleteDoc,
  onSnapshot,
  serverTimestamp,
  enableIndexedDbPersistence
} from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js';

// ─────────────────────────────────────────────────────────────
// CONFIGURACIÓN — reemplazá estos valores con los de tu proyecto
// en Firebase Console → Configuración del proyecto → Tu app web
// ─────────────────────────────────────────────────────────────
const firebaseConfig = {
  apiKey: 'AIzaSyDf49KWGdZp1C3t42LSopS_VuNiaabFZQw',
  authDomain: 'control-cirugias-c9c71.firebaseapp.com',
  projectId: 'control-cirugias-c9c71',
  storageBucket: 'control-cirugias-c9c71.firebasestorage.app',
  messagingSenderId: '714322418539',
  appId: '1:714322418539:web:523a8e5ad295d277b20a2e',
  measurementId: 'G-T7SBGEQ2G9'
};

// ─────────────────────────────────────────────────────────────
// INICIALIZACIÓN — con Promise para sincronizar con el script principal
// ─────────────────────────────────────────────────────────────
let app, db, cirugiasRef;
let readyResolve;
const readyPromise = new Promise(res => { readyResolve = res; });

try {
  app = initializeApp(firebaseConfig);
  db = getFirestore(app);
  cirugiasRef = collection(db, 'cirugias');

  // Persistencia offline (trabaja sin internet, sincroniza al reconectar)
  enableIndexedDbPersistence(db).catch(err => {
    if (err.code === 'failed-precondition') {
      console.warn('Firestore offline: múltiples tabs abiertas, solo una tiene persistencia');
    } else if (err.code === 'unimplemented') {
      console.warn('Firestore offline no soportado en este navegador');
    }
  });

  readyResolve(true);
} catch (err) {
  console.error('Firebase init error:', err);
  readyResolve(false);
}

// ─────────────────────────────────────────────────────────────
// HELPERS INTERNOS
// ─────────────────────────────────────────────────────────────
function normalizeValue(v) {
  if (v && typeof v.toDate === 'function') return v.toDate().toISOString();
  return v;
}

function normalizeRow(raw, docId) {
  const row = {};
  for (const [k, v] of Object.entries(raw || {})) row[k] = normalizeValue(v);
  row.id = String(row.id ?? docId ?? '');
  return row;
}

function sanitizeRowForSave(row) {
  const out = { ...row };
  const nowIso = new Date().toISOString();
  out.id = String(out.id ?? '');
  if (!out.createdAt) out.createdAt = nowIso;
  out.updatedAt = nowIso;
  // Firestore no acepta undefined — convertir a null
  for (const k of Object.keys(out)) {
    if (out[k] === undefined) out[k] = null;
  }
  return out;
}

// ─────────────────────────────────────────────────────────────
// API PÚBLICA
// ─────────────────────────────────────────────────────────────
async function upsertRow(row) {
  const sanitized = sanitizeRowForSave(row);
  const id = String(sanitized.id || Date.now());
  sanitized.id = id;
  await setDoc(doc(cirugiasRef, id), {
    ...sanitized,
    updatedAtServer: serverTimestamp()
  }, { merge: true });
  return id;
}

async function replaceAllRows(rows = []) {
  const BATCH_SIZE = 20;
  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const batch = rows.slice(i, i + BATCH_SIZE);
    await Promise.all(batch.map(r => upsertRow(r)));
  }
}

async function deleteRow(id) {
  await deleteDoc(doc(cirugiasRef, String(id)));
}

function listenRows(onRows, onError) {
  return onSnapshot(
    cirugiasRef,
    (snap) => {
      const rows = snap.docs.map(d => normalizeRow(d.data(), d.id));
      onRows(rows);
    },
    onError || ((err) => console.error('Firestore listener error:', err))
  );
}

async function exportAllRows() {
  const snap = await getDocs(cirugiasRef);
  return snap.docs.map(d => normalizeRow(d.data(), d.id));
}

// ─────────────────────────────────────────────────────────────
// EXPONER AL SCRIPT PRINCIPAL
// ─────────────────────────────────────────────────────────────
window.firestoreConnector = {
  ready: readyPromise,
  upsertRow,
  replaceAllRows,
  deleteRow,
  listenRows,
  exportAllRows
};

// Evento para que el script principal detecte la carga del módulo
window.dispatchEvent(new CustomEvent('firestoreReady'));

// firebase.js — Firestore connector v3 — Control de Cirugías
// Compatible con GitHub Pages | ES modules nativos | Sin bundler

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import {
  getFirestore, collection, doc, setDoc, getDocs,
  deleteDoc, onSnapshot, serverTimestamp,
  enableIndexedDbPersistence
} from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js';

// ── Configuración Firebase ──────────────────────────────────────────
// Reemplazá estos valores en Firebase Console → Configuración → Tu app
const firebaseConfig = {
  apiKey: 'AIzaSyDf49KWGdZp1C3t42LSopS_VuNiaabFZQw',
  authDomain: 'control-cirugias-c9c71.firebaseapp.com',
  projectId: 'control-cirugias-c9c71',
  storageBucket: 'control-cirugias-c9c71.firebasestorage.app',
  messagingSenderId: '714322418539',
  appId: '1:714322418539:web:523a8e5ad295d277b20a2e'
};

// ── Init ────────────────────────────────────────────────────────────
let readyResolve;
const readyPromise = new Promise(r => { readyResolve = r; });

let app, db, cirugiasRef;
try {
  app = initializeApp(firebaseConfig);
  db  = getFirestore(app);
  cirugiasRef = collection(db, 'cirugias');
  enableIndexedDbPersistence(db).catch(() => {});
  readyResolve(true);
} catch(e) {
  console.error('[Firebase] init error', e);
  readyResolve(false);
}

// ── Helpers internos ────────────────────────────────────────────────
function normVal(v) {
  if (v && typeof v.toDate === 'function') return v.toDate().toISOString().slice(0,10);
  return v;
}
function normRow(raw, docId) {
  const row = {};
  for (const [k,v] of Object.entries(raw||{})) row[k] = normVal(v);
  row.id = String(row.id ?? docId ?? '');
  return row;
}
function sanitize(row) {
  const out = { ...row };
  const now = new Date().toISOString();
  out.id = String(out.id || '');
  if (!out.createdAt) out.createdAt = now;
  out.updatedAt = now;
  for (const k of Object.keys(out)) if (out[k] === undefined) out[k] = null;
  return out;
}

// ── API pública ─────────────────────────────────────────────────────
async function upsertRow(row) {
  const s = sanitize(row);
  const id = String(s.id || Date.now());
  s.id = id;
  await setDoc(doc(cirugiasRef, id), { ...s, _srv: serverTimestamp() }, { merge: true });
  return id;
}

async function replaceAllRows(rows = []) {
  const CHUNK = 20;
  for (let i = 0; i < rows.length; i += CHUNK) {
    await Promise.all(rows.slice(i, i+CHUNK).map(r => upsertRow(r)));
  }
}

async function deleteRow(id) {
  await deleteDoc(doc(cirugiasRef, String(id)));
}

function listenRows(onRows, onErr) {
  return onSnapshot(cirugiasRef,
    snap => onRows(snap.docs.map(d => normRow(d.data(), d.id))),
    onErr || (e => console.error('[Firestore] listener', e))
  );
}

async function exportAllRows() {
  const snap = await getDocs(cirugiasRef);
  return snap.docs.map(d => normRow(d.data(), d.id));
}

// ── Exponer al script principal ─────────────────────────────────────
window.firestoreConnector = { ready: readyPromise, upsertRow, replaceAllRows, deleteRow, listenRows, exportAllRows };
window.dispatchEvent(new CustomEvent('firestoreReady'));

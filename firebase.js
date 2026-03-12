import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import {
  getFirestore,
  collection,
  doc,
  setDoc,
  getDocs,
  deleteDoc,
  onSnapshot,
  serverTimestamp
} from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js';

const firebaseConfig = {
  apiKey: 'AIzaSyDf49KWGdZp1C3t42LSopS_VuNiaabFZQw',
  authDomain: 'control-cirugias-c9c71.firebaseapp.com',
  projectId: 'control-cirugias-c9c71',
  storageBucket: 'control-cirugias-c9c71.firebasestorage.app',
  messagingSenderId: '714322418539',
  appId: '1:714322418539:web:523a8e5ad295d277b20a2e',
  measurementId: 'G-T7SBGEQ2G9'
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const cirugiasRef = collection(db, 'cirugias');

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
  return out;
}

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
  const tasks = (rows || []).map((r) => upsertRow(r));
  await Promise.all(tasks);
}

async function deleteRow(id) {
  await deleteDoc(doc(cirugiasRef, String(id)));
}

function listenRows(onRows, onError) {
  return onSnapshot(cirugiasRef, (snap) => {
    const rows = snap.docs.map((d) => normalizeRow(d.data(), d.id));
    onRows(rows);
  }, onError);
}

async function exportAllRows() {
  const snap = await getDocs(cirugiasRef);
  return snap.docs.map((d) => normalizeRow(d.data(), d.id));
}

window.firestoreConnector = {
  ready: Promise.resolve(true),
  upsertRow,
  replaceAllRows,
  deleteRow,
  listenRows,
  exportAllRows
};

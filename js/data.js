import { db, appConfig } from './firebase.js';
import {
  collection,
  query,
  where,
  orderBy,
  limit,
  startAfter,
  getDocs,
  getDoc,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  serverTimestamp
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';
import { safeGetJSON, safeSetJSON } from './storage.js';

const COLLECTION = appConfig.businessCollection;
const PAGE_SIZE = 20;

let pageCursors = [null];
let lastFilterHash = '';

export function getPageSize() {
  return PAGE_SIZE;
}

export function getCachedRows() {
  return safeGetJSON('rows-cache', []);
}

function buildFilterHash(filters) {
  return JSON.stringify(filters || {});
}

function baseQuery(filters = {}) {
  const constraints = [];
  if (filters.status) constraints.push(where('status', '==', filters.status));
  if (filters.eye) constraints.push(where('eye', '==', filters.eye));
  constraints.push(orderBy('updatedAt', 'desc'));
  return query(collection(db, COLLECTION), ...constraints);
}

export async function fetchPage(filters = {}, page = 1) {
  const hash = buildFilterHash(filters);
  if (hash !== lastFilterHash) {
    lastFilterHash = hash;
    pageCursors = [null];
  }

  if (!pageCursors[page - 1] && page > 1) {
    throw new Error('No se puede cargar esta página sin la anterior.');
  }

  let q = query(baseQuery(filters), limit(PAGE_SIZE));
  const startCursor = pageCursors[page - 1];
  if (startCursor) {
    q = query(baseQuery(filters), startAfter(startCursor), limit(PAGE_SIZE));
  }

  const snap = await getDocs(q);
  const docs = snap.docs;
  const rows = docs.map((d) => ({ id: d.id, ...d.data() }));

  const lastVisible = docs.length ? docs[docs.length - 1] : null;
  pageCursors[page] = lastVisible;

  safeSetJSON('rows-cache', rows);
  return {
    rows,
    hasPrev: page > 1,
    hasNext: docs.length === PAGE_SIZE
  };
}

export function applyLocalSearch(rows, text) {
  const q = String(text || '').trim().toLowerCase();
  if (!q) return rows;
  return rows.filter((row) => {
    const source = [
      row.patientName,
      row.dni,
      row.lens,
      row.administrativo,
      row.status,
      row.autorizacion
    ].join(' ').toLowerCase();
    return source.includes(q);
  });
}

export async function createCirugia(payload) {
  const now = serverTimestamp();
  const clean = {
    ...payload,
    createdAt: now,
    updatedAt: now
  };
  const ref = await addDoc(collection(db, COLLECTION), clean);
  return ref.id;
}

export async function updateCirugia(id, payload) {
  const clean = {
    ...payload,
    updatedAt: serverTimestamp()
  };
  await updateDoc(doc(db, COLLECTION, id), clean);
}

export async function deleteCirugia(id) {
  await deleteDoc(doc(db, COLLECTION, id));
}

export async function getCirugiaById(id) {
  const snap = await getDoc(doc(db, COLLECTION, id));
  if (!snap.exists()) return null;
  return { id: snap.id, ...snap.data() };
}

import { db } from './firebase.js';
import { collection, addDoc, updateDoc, doc, getDoc, getDocs, query, where, orderBy, limit, startAfter, Timestamp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';
import { safeGet, safeSet } from './storage.js';

const PAGE_SIZE = 20;
let cursor = null;
let lastQueryMeta = {};

export function getCachedRecords() {
  return safeGet('records_cache', []);
}

export async function fetchRecords({ status = '', eye = '', text = '', reset = true } = {}) {
  if (reset || JSON.stringify(lastQueryMeta) !== JSON.stringify({ status, eye, text })) {
    cursor = null;
    lastQueryMeta = { status, eye, text };
  }

  let q = query(collection(db, 'surgeries'), orderBy('updatedAt', 'desc'), limit(PAGE_SIZE));
  if (status) q = query(collection(db, 'surgeries'), where('status', '==', status), orderBy('updatedAt', 'desc'), limit(PAGE_SIZE));
  if (eye) q = query(collection(db, 'surgeries'), where('eye', '==', eye), orderBy('updatedAt', 'desc'), limit(PAGE_SIZE));
  if (cursor) q = query(q, startAfter(cursor));

  const snap = await getDocs(q);
  const records = snap.docs.map((d) => ({ id: d.id, ...d.data() }));
  const filtered = text
    ? records.filter((r) => `${r.patientName} ${r.dni} ${r.lens}`.toLowerCase().includes(text.toLowerCase()))
    : records;
  cursor = snap.docs.at(-1) || null;
  safeSet('records_cache', filtered);
  return { records: filtered, hasMore: Boolean(cursor) };
}

export async function createRecord(payload) {
  payload.createdAt = Timestamp.now();
  payload.updatedAt = Timestamp.now();
  const ref = await addDoc(collection(db, 'surgeries'), payload);
  return ref.id;
}

export async function patchRecord(id, payload) {
  payload.updatedAt = Timestamp.now();
  await updateDoc(doc(db, 'surgeries', id), payload);
}

export async function readRecord(id) {
  const snap = await getDoc(doc(db, 'surgeries', id));
  return snap.exists() ? { id: snap.id, ...snap.data() } : null;
}

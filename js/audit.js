import { db } from './firebase.js';
import { collection, addDoc, Timestamp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

export async function logAudit({ userId, action, docId, changedFields = [], oldValues = {}, newValues = {} }) {
  await addDoc(collection(db, 'audit_log'), {
    userId,
    action,
    docId,
    changedFields,
    oldValues,
    newValues,
    timestamp: Timestamp.now()
  });
}

export function diffFields(oldRecord, newRecord) {
  const changedFields = Object.keys(newRecord).filter((k) => JSON.stringify(oldRecord?.[k]) !== JSON.stringify(newRecord[k]));
  const oldValues = {};
  const newValues = {};
  for (const key of changedFields) {
    oldValues[key] = oldRecord?.[key] ?? null;
    newValues[key] = newRecord[key] ?? null;
  }
  return { changedFields, oldValues, newValues };
}

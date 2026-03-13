import { db, appConfig } from './firebase.js';
import { collection, addDoc, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

const AUDIT = appConfig.auditCollection;

export function diffChanges(oldObj = {}, newObj = {}) {
  const changedFields = [];
  const oldValues = {};
  const newValues = {};

  const keys = new Set([...Object.keys(oldObj || {}), ...Object.keys(newObj || {})]);
  for (const key of keys) {
    const before = oldObj?.[key] ?? null;
    const after = newObj?.[key] ?? null;
    if (JSON.stringify(before) !== JSON.stringify(after)) {
      changedFields.push(key);
      oldValues[key] = before;
      newValues[key] = after;
    }
  }
  return { changedFields, oldValues, newValues };
}

export async function registerAudit({ userId, username, action, docId, changedFields, oldValues, newValues }) {
  await addDoc(collection(db, AUDIT), {
    userId,
    username,
    action,
    docId,
    timestamp: serverTimestamp(),
    changedFields: changedFields || [],
    oldValues: oldValues || {},
    newValues: newValues || {}
  });
}

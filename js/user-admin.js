import { db, appConfig } from './firebase.js';
import { doc, setDoc, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

const USERS = appConfig.usersCollection;

export function readUserForm() {
  return {
    uid: document.getElementById('u-uid').value.trim(),
    username: document.getElementById('u-username').value.trim(),
    displayName: document.getElementById('u-displayName').value.trim(),
    role: document.getElementById('u-role').value,
    authEmail: document.getElementById('u-authEmail').value.trim(),
    active: document.getElementById('u-active').value === 'true',
    mustChangePassword: document.getElementById('u-mustChangePassword').value === 'true'
  };
}

export async function upsertUserProfile(data, actor) {
  if (!data.uid || !data.username || !data.displayName || !data.role || !data.authEmail) {
    throw new Error('Completá todos los campos de usuario.');
  }

  const username_lc = data.username.toLowerCase();
  await setDoc(doc(db, USERS, data.uid), {
    username: data.username,
    username_lc,
    displayName: data.displayName,
    role: data.role,
    authEmail: data.authEmail,
    active: data.active,
    mustChangePassword: data.mustChangePassword,
    updatedAt: serverTimestamp(),
    updatedBy: actor?.uid || 'unknown'
  }, { merge: true });
}

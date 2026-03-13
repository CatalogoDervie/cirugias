import { auth, db, appConfig } from './firebase.js';
import {
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updatePassword
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js';
import {
  collection,
  query,
  where,
  limit,
  getDocs,
  doc,
  getDoc,
  updateDoc,
  serverTimestamp
} from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

const USERS = appConfig.usersCollection;

export async function resolveUsernameToProfile(usernameRaw) {
  const username = String(usernameRaw || '').trim().toLowerCase();
  if (!username) {
    throw new Error('Ingresá usuario.');
  }

  const q = query(
    collection(db, USERS),
    where('username_lc', '==', username),
    limit(1)
  );
  const snap = await getDocs(q);
  if (snap.empty) {
    throw new Error('Usuario no encontrado.');
  }
  const docSnap = snap.docs[0];
  const profile = { uid: docSnap.id, ...docSnap.data() };

  if (!profile.active) {
    throw new Error('Usuario inactivo.');
  }
  if (!profile.authEmail) {
    throw new Error('Usuario sin email técnico configurado.');
  }
  return profile;
}

export async function loginWithUsername(username, password) {
  const profile = await resolveUsernameToProfile(username);
  const credential = await signInWithEmailAndPassword(auth, profile.authEmail, password);
  const fullProfile = await getUserProfile(credential.user.uid);
  if (!fullProfile.active) {
    await signOut(auth);
    throw new Error('Usuario inactivo.');
  }
  return { user: credential.user, profile: fullProfile };
}

export async function logout() {
  await signOut(auth);
}

export function observeSession(handler) {
  return onAuthStateChanged(auth, handler);
}

export async function getUserProfile(uid) {
  const snap = await getDoc(doc(db, USERS, uid));
  if (!snap.exists()) {
    return {
      uid,
      username: 'sin-perfil',
      displayName: 'Usuario sin perfil',
      role: 'readonly',
      active: false,
      mustChangePassword: false
    };
  }
  return { uid: snap.id, ...snap.data() };
}

export async function changePasswordAndClearFlag(newPassword) {
  if (!auth.currentUser) {
    throw new Error('Sesión no disponible.');
  }
  await updatePassword(auth.currentUser, newPassword);
  await updateDoc(doc(db, USERS, auth.currentUser.uid), {
    mustChangePassword: false,
    updatedAt: serverTimestamp()
  });
}

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js';
import { getAuth, setPersistence, browserLocalPersistence } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

let cfg;
try {
  cfg = await import('./config.js');
} catch {
  throw new Error('Falta js/config.js. Copiar js/config.example.js y completar valores.');
}

export const firebaseConfig = cfg.firebaseConfig;
export const appConfig = cfg.appConfig || {
  appName: 'CONTROL DE CIRUGÍAS',
  businessCollection: 'cirugias',
  usersCollection: 'users',
  auditCollection: 'audit_log'
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
await setPersistence(auth, browserLocalPersistence);
const db = getFirestore(app);

export { app, auth, db };

import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js';
import { getAuth, setPersistence, browserLocalPersistence } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js';
import { getFirestore } from 'https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js';

let firebaseConfig;
try {
  ({ firebaseConfig } = await import('./config.js'));
} catch {
  throw new Error('Falta js/config.js. Copiar desde js/config.example.js y completar credenciales.');
}

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
await setPersistence(auth, browserLocalPersistence);
const db = getFirestore(app);

export { app, auth, db };

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.10.0/firebase-app.js";
import {
  getFirestore,
  collection,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  onSnapshot,
  query,
  orderBy,
  serverTimestamp
} from "https://www.gstatic.com/firebasejs/11.10.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyDf49KWGdZp1C3t42LSopS_VuNiaabFZQw",
  authDomain: "control-cirugias-c9c71.firebaseapp.com",
  projectId: "control-cirugias-c9c71",
  storageBucket: "control-cirugias-c9c71.firebasestorage.app",
  messagingSenderId: "714322418539",
  appId: "1:714322418539:web:523a8e5ad295d277b20a2e",
  measurementId: "G-T7SBGEQ2G9"
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

export {
  db,
  collection,
  addDoc,
  updateDoc,
  deleteDoc,
  doc,
  onSnapshot,
  query,
  orderBy,
  serverTimestamp
};

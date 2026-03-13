import { login, logout, observeSession, getUserProfile } from './auth.js';
import { fetchRecords, createRecord, patchRecord, readRecord, getCachedRecords } from './data.js';
import { buildAlerts } from './alerts.js';
import { logAudit, diffFields } from './audit.js';
import { copyBackupToClipboard } from './backup.js';
import { toggleView, setUserBadge, renderRecords, renderAlerts, fillForm, readForm, showEditor, setPageIndicator } from './ui.js';

let currentUser = null;
let profile = { role: 'readonly' };
let currentRecords = getCachedRecords();
let page = 1;

const canEdit = () => ['admin', 'operador'].includes(profile.role);

async function refresh(reset = true) {
  const status = document.getElementById('filter-status').value;
  const eye = document.getElementById('filter-eye').value;
  const text = document.getElementById('search-input').value.trim();
  const { records, hasMore } = await fetchRecords({ status, eye, text, reset });
  currentRecords = records;
  renderRecords(records, profile.role);
  renderAlerts(buildAlerts(records));
  setPageIndicator(page, hasMore);
}

function showError(text) { document.getElementById('login-error').textContent = text; }

document.getElementById('login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showError('');
  try {
    await login(email.value, password.value);
  } catch {
    showError('Credenciales inválidas o usuario sin acceso.');
  }
});

document.getElementById('logout-btn').addEventListener('click', async () => { await logout(); });

observeSession(async (user) => {
  currentUser = user;
  toggleView(Boolean(user));
  if (!user) return;
  profile = await getUserProfile(user.uid);
  setUserBadge(profile);
  document.getElementById('new-record-btn').disabled = !canEdit();
  await refresh(true);
});

document.getElementById('search-input').addEventListener('input', async () => { page = 1; await refresh(true); });
document.getElementById('filter-status').addEventListener('change', async () => { page = 1; await refresh(true); });
document.getElementById('filter-eye').addEventListener('change', async () => { page = 1; await refresh(true); });

document.getElementById('prev-page').addEventListener('click', async () => {
  if (page === 1) return;
  page -= 1;
  await refresh(true);
});

document.getElementById('next-page').addEventListener('click', async () => {
  page += 1;
  await refresh(false);
});

document.getElementById('new-record-btn').addEventListener('click', () => {
  if (!canEdit()) return;
  fillForm(null);
  showEditor(true, 'Nuevo registro');
});

document.getElementById('cancel-btn').addEventListener('click', () => showEditor(false));

document.getElementById('records-body').addEventListener('click', async (e) => {
  const id = e.target.dataset.id;
  if (!id || !canEdit()) return;
  const record = await readRecord(id);
  fillForm(record);
  showEditor(true, 'Editar registro');
});

document.getElementById('record-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!canEdit()) return;
  const id = document.getElementById('record-id').value;
  const payload = readForm();

  try {
    if (id) {
      const oldRecord = await readRecord(id);
      await patchRecord(id, payload);
      await logAudit({ userId: currentUser.uid, action: 'update', docId: id, ...diffFields(oldRecord, payload) });
    } else {
      const newId = await createRecord(payload);
      await logAudit({ userId: currentUser.uid, action: 'create', docId: newId, changedFields: Object.keys(payload), oldValues: {}, newValues: payload });
    }
    showEditor(false);
    await refresh(true);
    showError('Guardado con éxito.');
  } catch (err) {
    console.error(err);
    showError('No se pudo guardar el registro.');
  }
});

window.copyBackup = async () => {
  const bytes = await copyBackupToClipboard(currentRecords);
  alert(`Backup copiado al portapapeles (${bytes} caracteres).`);
};

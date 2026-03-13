import {
  loginWithUsername,
  logout,
  observeSession,
  getUserProfile,
  changePasswordAndClearFlag
} from './auth.js';
import {
  fetchPage,
  applyLocalSearch,
  createCirugia,
  updateCirugia,
  deleteCirugia,
  getCirugiaById,
  getCachedRows
} from './data.js';
import { buildAlerts } from './alerts.js';
import { registerAudit, diffChanges } from './audit.js';
import { copyBackupText } from './backup.js';
import {
  setMessage,
  toggleBlock,
  setSessionBadge,
  renderAlerts,
  renderRows,
  setPagination,
  openEditor,
  closeEditor,
  readRecordForm
} from './ui.js';
import { readUserForm, upsertUserProfile } from './user-admin.js';

let currentUser = null;
let currentProfile = null;
let currentRows = getCachedRows();
let page = 1;
let hasPrev = false;
let hasNext = false;

function canEdit() {
  return currentProfile?.role === 'admin' || currentProfile?.role === 'operador';
}

function canDelete() {
  return currentProfile?.role === 'admin';
}

function canAdminUsers() {
  return currentProfile?.role === 'admin';
}

function ensureFirebaseReady() {
  toggleBlock('firebase-fallback', false);
}

function showFirebaseFail(error) {
  console.error(error);
  document.getElementById('firebase-fallback-text').textContent = `No se pudo inicializar Firebase: ${error.message || error}`;
  toggleBlock('firebase-fallback', true);
  toggleBlock('login-view', false);
  toggleBlock('password-change-view', false);
  toggleBlock('main-view', false);
}

function collectFilters() {
  return {
    status: document.getElementById('status-filter').value,
    eye: document.getElementById('eye-filter').value
  };
}

async function refreshTable(resetPage = false) {
  if (!currentUser) return;
  if (resetPage) page = 1;

  const filters = collectFilters();
  const response = await fetchPage(filters, page);
  const searchText = document.getElementById('search-input').value;
  const rowsForView = applyLocalSearch(response.rows, searchText);

  currentRows = response.rows;
  hasPrev = response.hasPrev;
  hasNext = response.hasNext;

  renderRows(rowsForView, currentProfile.role);
  renderAlerts(buildAlerts(rowsForView));
  setPagination(page, hasPrev, hasNext);
}

function goToLogin() {
  toggleBlock('login-view', true);
  toggleBlock('password-change-view', false);
  toggleBlock('main-view', false);
  setMessage('login-message', '');
  setMessage('main-message', '');
}

function goToPasswordChange() {
  toggleBlock('login-view', false);
  toggleBlock('password-change-view', true);
  toggleBlock('main-view', false);
  setMessage('password-change-message', '');
}

function goToMain() {
  toggleBlock('login-view', false);
  toggleBlock('password-change-view', false);
  toggleBlock('main-view', true);
  toggleBlock('user-admin-section', canAdminUsers());
  document.getElementById('new-record-btn').disabled = !canEdit();
  setSessionBadge(currentProfile);
}

async function handleSession(user) {
  currentUser = user;

  if (!user) {
    currentProfile = null;
    goToLogin();
    return;
  }

  currentProfile = await getUserProfile(user.uid);
  if (!currentProfile.active) {
    await logout();
    goToLogin();
    setMessage('login-message', 'Usuario inactivo.', 'error');
    return;
  }

  if (currentProfile.mustChangePassword) {
    goToPasswordChange();
    return;
  }

  goToMain();
  await refreshTable(true);
}

function attachEvents() {
  document.getElementById('login-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage('login-message', '');

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
      await loginWithUsername(username, password);
      setMessage('login-message', 'Ingreso correcto.', 'success');
    } catch (error) {
      setMessage('login-message', error.message || 'No se pudo iniciar sesión.', 'error');
    }
  });

  document.getElementById('password-change-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    setMessage('password-change-message', '');

    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;

    if (newPassword.length < 10) {
      setMessage('password-change-message', 'La nueva contraseña debe tener al menos 10 caracteres.', 'error');
      return;
    }
    if (newPassword !== confirmPassword) {
      setMessage('password-change-message', 'La confirmación no coincide.', 'error');
      return;
    }

    try {
      await changePasswordAndClearFlag(newPassword);
      setMessage('password-change-message', 'Contraseña actualizada. Reingresá al sistema.', 'success');
      await logout();
    } catch (error) {
      setMessage('password-change-message', error.message || 'No se pudo cambiar la contraseña.', 'error');
    }
  });

  document.getElementById('logout-btn').addEventListener('click', async () => {
    await logout();
  });

  document.getElementById('search-input').addEventListener('input', async () => {
    try {
      await refreshTable(false);
    } catch (error) {
      setMessage('main-message', error.message, 'error');
    }
  });

  document.getElementById('status-filter').addEventListener('change', async () => {
    try {
      await refreshTable(true);
    } catch (error) {
      setMessage('main-message', error.message, 'error');
    }
  });

  document.getElementById('eye-filter').addEventListener('change', async () => {
    try {
      await refreshTable(true);
    } catch (error) {
      setMessage('main-message', error.message, 'error');
    }
  });

  document.getElementById('prev-btn').addEventListener('click', async () => {
    if (!hasPrev) return;
    page -= 1;
    await refreshTable(false);
  });

  document.getElementById('next-btn').addEventListener('click', async () => {
    if (!hasNext) return;
    page += 1;
    await refreshTable(false);
  });

  document.getElementById('new-record-btn').addEventListener('click', () => {
    if (!canEdit()) return;
    openEditor(null);
  });

  document.getElementById('cancel-edit-btn').addEventListener('click', () => {
    closeEditor();
  });

  document.getElementById('records-tbody').addEventListener('click', async (event) => {
    const btn = event.target;
    const id = btn?.dataset?.id;
    if (!id) return;

    if (btn.classList.contains('edit-btn')) {
      if (!canEdit()) return;
      const row = await getCirugiaById(id);
      if (!row) {
        setMessage('main-message', 'Registro no encontrado.', 'error');
        return;
      }
      openEditor(row);
      return;
    }

    if (btn.classList.contains('delete-btn')) {
      if (!canDelete()) return;
      const oldRow = await getCirugiaById(id);
      if (!oldRow) return;
      await deleteCirugia(id);
      const delta = diffChanges(oldRow, {});
      await registerAudit({
        userId: currentUser.uid,
        username: currentProfile.username,
        action: 'delete',
        docId: id,
        changedFields: delta.changedFields,
        oldValues: delta.oldValues,
        newValues: {}
      });
      setMessage('main-message', 'Registro eliminado.', 'success');
      await refreshTable(true);
    }
  });

  document.getElementById('record-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!canEdit()) return;

    const id = document.getElementById('record-id').value;
    const payload = readRecordForm();

    if (!payload.patientName || !payload.dni || !payload.eye || !payload.lens || !payload.status) {
      setMessage('main-message', 'Completá los campos obligatorios del registro.', 'error');
      return;
    }

    try {
      if (id) {
        const oldData = await getCirugiaById(id);
        await updateCirugia(id, payload);
        const delta = diffChanges(oldData, payload);
        await registerAudit({
          userId: currentUser.uid,
          username: currentProfile.username,
          action: 'update',
          docId: id,
          changedFields: delta.changedFields,
          oldValues: delta.oldValues,
          newValues: delta.newValues
        });
        setMessage('main-message', 'Registro actualizado.', 'success');
      } else {
        const newId = await createCirugia(payload);
        const delta = diffChanges({}, payload);
        await registerAudit({
          userId: currentUser.uid,
          username: currentProfile.username,
          action: 'create',
          docId: newId,
          changedFields: delta.changedFields,
          oldValues: {},
          newValues: delta.newValues
        });
        setMessage('main-message', 'Registro creado.', 'success');
      }

      closeEditor();
      await refreshTable(true);
    } catch (error) {
      console.error(error);
      setMessage('main-message', error.message || 'No se pudo guardar el registro.', 'error');
    }
  });

  document.getElementById('copy-backup-btn').addEventListener('click', async () => {
    try {
      const text = await copyBackupText(currentRows);
      setMessage('main-message', `Backup copiado al portapapeles (${text.length} caracteres).`, 'success');
    } catch (error) {
      setMessage('main-message', 'No se pudo copiar backup.', 'error');
    }
  });

  document.getElementById('user-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!canAdminUsers()) return;

    const data = readUserForm();
    try {
      await upsertUserProfile(data, currentUser);
      await registerAudit({
        userId: currentUser.uid,
        username: currentProfile.username,
        action: 'upsert_user_profile',
        docId: data.uid,
        changedFields: Object.keys(data),
        oldValues: {},
        newValues: data
      });
      setMessage('user-message', 'Perfil de usuario guardado correctamente.', 'success');
    } catch (error) {
      setMessage('user-message', error.message || 'No se pudo guardar el perfil de usuario.', 'error');
    }
  });
}

async function bootstrap() {
  try {
    ensureFirebaseReady();
    attachEvents();
    observeSession(async (user) => {
      try {
        await handleSession(user);
      } catch (error) {
        console.error(error);
        setMessage('login-message', 'Error en sesión. Reintentá.', 'error');
        goToLogin();
      }
    });
  } catch (error) {
    showFirebaseFail(error);
  }
}

bootstrap();

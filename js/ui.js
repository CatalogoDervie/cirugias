function esc(v) { return String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }

export function toggleView(isLogged) {
  document.getElementById('login-view').classList.toggle('hidden', isLogged);
  document.getElementById('main-view').classList.toggle('hidden', !isLogged);
}

export function setUserBadge(profile) {
  document.getElementById('user-badge').innerHTML = `${esc(profile.displayName || 'Usuario')} <span class="badge">${esc(profile.role || 'readonly')}</span>`;
}

export function renderRecords(records, role) {
  const tbody = document.getElementById('records-body');
  tbody.innerHTML = records.map((r) => `
    <tr data-id="${r.id}">
      <td>${esc(r.patientName)}</td>
      <td>${esc(r.dni)}</td>
      <td>${esc(r.eye)}</td>
      <td>${esc(r.lens)}</td>
      <td>${esc(r.status)}</td>
      <td>${esc(r.surgeryDate || '-')}</td>
      <td>${esc(r.authorization || '-')}</td>
      <td>${role === 'readonly' ? '-' : `<button class="edit-btn" data-id="${r.id}">Editar</button>`}</td>
    </tr>`).join('');
}

export function renderAlerts(alerts) {
  document.getElementById('alerts').innerHTML = alerts.map((a) => `<div class="alert">${esc(a)}</div>`).join('') || '<div class="alert">Sin alertas críticas.</div>';
}

export function fillForm(record) {
  document.getElementById('record-id').value = record?.id || '';
  document.getElementById('f-patient').value = record?.patientName || '';
  document.getElementById('f-dni').value = record?.dni || '';
  document.getElementById('f-eye').value = record?.eye || 'OD';
  document.getElementById('f-lens').value = record?.lens || '';
  document.getElementById('f-preop').value = record?.preop || '';
  document.getElementById('f-status').value = record?.status || 'pendiente';
  document.getElementById('f-surgery-date').value = record?.surgeryDate || '';
  document.getElementById('f-authorization').value = record?.authorization || 'pendiente';
  document.getElementById('f-owner').value = record?.owner || '';
  document.getElementById('f-notes').value = record?.notes || '';
}

export function readForm() {
  return {
    patientName: document.getElementById('f-patient').value.trim(),
    dni: document.getElementById('f-dni').value.trim(),
    eye: document.getElementById('f-eye').value,
    lens: document.getElementById('f-lens').value.trim(),
    preop: document.getElementById('f-preop').value.trim(),
    status: document.getElementById('f-status').value,
    surgeryDate: document.getElementById('f-surgery-date').value,
    authorization: document.getElementById('f-authorization').value,
    owner: document.getElementById('f-owner').value.trim(),
    notes: document.getElementById('f-notes').value.trim()
  };
}

export function showEditor(show, title = 'Nuevo registro') {
  document.getElementById('editor').classList.toggle('hidden', !show);
  document.getElementById('editor-title').textContent = title;
}

export function setPageIndicator(page, hasMore) {
  document.getElementById('page-indicator').textContent = `Página ${page}`;
  document.getElementById('next-page').disabled = !hasMore;
}

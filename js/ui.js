function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (s) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[s]));
}

export function setMessage(elId, text, type = '') {
  const el = document.getElementById(elId);
  if (!el) return;
  el.textContent = text || '';
  el.className = 'message';
  if (type) el.classList.add(type);
}

export function toggleBlock(id, show) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('hidden', !show);
}

export function setSessionBadge(profile) {
  const role = esc(profile?.role || 'readonly');
  const username = esc(profile?.username || 'sin-usuario');
  const displayName = esc(profile?.displayName || 'Sin nombre');
  document.getElementById('session-badge').innerHTML = `${displayName} | usuario: ${username} | rol: ${role}`;
}

export function renderAlerts(alerts = []) {
  const wrap = document.getElementById('alerts-wrap');
  if (!alerts.length) {
    wrap.innerHTML = '<div class="alert-item">Sin alertas administrativas críticas.</div>';
    return;
  }
  wrap.innerHTML = alerts.map((a) => `<div class="alert-item">${esc(a)}</div>`).join('');
}

export function renderRows(rows = [], role = 'readonly') {
  const tbody = document.getElementById('records-tbody');
  const canEdit = role === 'admin' || role === 'operador';
  const canDelete = role === 'admin';

  if (!rows.length) {
    tbody.innerHTML = '<tr><td colspan="9">Sin registros para mostrar.</td></tr>';
    return;
  }

  tbody.innerHTML = rows.map((row) => {
    const editButton = canEdit ? `<button type="button" class="edit-btn" data-id="${esc(row.id)}">Editar</button>` : '';
    const deleteButton = canDelete ? `<button type="button" class="delete-btn btn-secondary" data-id="${esc(row.id)}">Eliminar</button>` : '';
    const actions = editButton || deleteButton ? `<div class="row-actions">${editButton}${deleteButton}</div>` : '-';

    return `
      <tr>
        <td>${esc(row.patientName)}</td>
        <td>${esc(row.dni)}</td>
        <td>${esc(row.eye)}</td>
        <td>${esc(row.lens)}</td>
        <td>${esc(row.status)}</td>
        <td>${esc(row.fechaCirugia || '-')}</td>
        <td>${esc(row.autorizacion || '-')}</td>
        <td>${esc(row.administrativo || '-')}</td>
        <td>${actions}</td>
      </tr>
    `;
  }).join('');
}

export function setPagination(page, hasPrev, hasNext) {
  document.getElementById('page-indicator').textContent = `Página ${page}`;
  document.getElementById('prev-btn').disabled = !hasPrev;
  document.getElementById('next-btn').disabled = !hasNext;
}

export function openEditor(record = null) {
  toggleBlock('editor-section', true);
  document.getElementById('editor-title').textContent = record ? 'Editar registro' : 'Nuevo registro';
  document.getElementById('record-id').value = record?.id || '';
  document.getElementById('f-patientName').value = record?.patientName || '';
  document.getElementById('f-dni').value = record?.dni || '';
  document.getElementById('f-eye').value = record?.eye || 'OD';
  document.getElementById('f-lens').value = record?.lens || '';
  document.getElementById('f-prequirurgico').value = record?.prequirurgico || '';
  document.getElementById('f-status').value = record?.status || 'pendiente';
  document.getElementById('f-fechaCirugia').value = record?.fechaCirugia || '';
  document.getElementById('f-autorizacion').value = record?.autorizacion || 'pendiente';
  document.getElementById('f-administrativo').value = record?.administrativo || '';
  document.getElementById('f-notas').value = record?.notas || '';
}

export function closeEditor() {
  toggleBlock('editor-section', false);
}

export function readRecordForm() {
  return {
    patientName: document.getElementById('f-patientName').value.trim(),
    dni: document.getElementById('f-dni').value.trim(),
    eye: document.getElementById('f-eye').value,
    lens: document.getElementById('f-lens').value.trim(),
    prequirurgico: document.getElementById('f-prequirurgico').value.trim(),
    status: document.getElementById('f-status').value,
    fechaCirugia: document.getElementById('f-fechaCirugia').value,
    autorizacion: document.getElementById('f-autorizacion').value,
    administrativo: document.getElementById('f-administrativo').value.trim(),
    notas: document.getElementById('f-notas').value.trim()
  };
}

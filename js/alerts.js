function daysUntil(dateIso) {
  if (!dateIso) return null;
  const now = new Date();
  const target = new Date(`${dateIso}T00:00:00`);
  const ms = target.getTime() - new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  return Math.floor(ms / 86400000);
}

export function buildAlerts(rows = []) {
  const alerts = [];
  for (const row of rows) {
    if (row.autorizacion === 'pendiente') {
      alerts.push(`Autorización pendiente: ${row.patientName} (${row.dni}).`);
    }
    const diff = daysUntil(row.fechaCirugia);
    if (diff !== null && diff >= 0 && diff <= 3 && row.status !== 'realizado' && row.status !== 'cancelado') {
      alerts.push(`Cirugía próxima (${diff} día/s): ${row.patientName} - ${row.fechaCirugia}.`);
    }
  }
  return alerts.slice(0, 12);
}

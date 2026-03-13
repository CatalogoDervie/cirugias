export function buildAlerts(records) {
  const today = new Date();
  return records.flatMap((r) => {
    const out = [];
    if (r.authorization === 'pendiente') {
      out.push(`Autorización pendiente: ${r.patientName} (${r.dni})`);
    }
    if (r.surgeryDate) {
      const d = new Date(r.surgeryDate + 'T00:00:00');
      const diff = Math.ceil((d - today) / 86400000);
      if (diff >= 0 && diff <= 3 && r.status !== 'realizado') {
        out.push(`Cirugía próxima (${diff} día/s): ${r.patientName} - ${r.surgeryDate}`);
      }
    }
    return out;
  });
}

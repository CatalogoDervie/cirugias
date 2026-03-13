export function buildBackupText(rows = []) {
  return JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      rows
    },
    null,
    2
  );
}

export async function copyBackupText(rows = []) {
  const text = buildBackupText(rows);
  await navigator.clipboard.writeText(text);
  return text;
}

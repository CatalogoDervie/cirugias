export function toBackupText(records) {
  return JSON.stringify({ exportedAt: new Date().toISOString(), records }, null, 2);
}

export async function copyBackupToClipboard(records) {
  const text = toBackupText(records);
  await navigator.clipboard.writeText(text);
  return text.length;
}

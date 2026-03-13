const PREFIX = 'cirugias.v2.';

export function safeGet(key, fallback = null) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(PREFIX + key);
    return fallback;
  }
}

export function safeSet(key, value) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch (error) {
    console.error('No se pudo persistir caché local.', error);
  }
}

export function safeRemove(key) {
  localStorage.removeItem(PREFIX + key);
}

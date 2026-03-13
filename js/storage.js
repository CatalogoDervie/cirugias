const PREFIX = 'control-cirugias.v3.';

export function safeGetJSON(key, fallback) {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch {
    localStorage.removeItem(PREFIX + key);
    return fallback;
  }
}

export function safeSetJSON(key, value) {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
    return true;
  } catch (error) {
    console.error('Error al guardar en caché local', error);
    return false;
  }
}

export function safeRemove(key) {
  localStorage.removeItem(PREFIX + key);
}

export function clearAllAppCache() {
  Object.keys(localStorage)
    .filter((k) => k.startsWith(PREFIX))
    .forEach((k) => localStorage.removeItem(k));
}

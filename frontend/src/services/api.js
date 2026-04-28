import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 300000,
});

export function resolveMediaUrl(url) {
  if (!url) return null;
  if (url.startsWith('http') || url.startsWith('data:')) return url;
  const path = url.startsWith('/') ? url : `/${url}`;
  const apiBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  if (apiBase.startsWith('http') && path.startsWith('/media/')) {
    return `${apiBase.replace(/\/api\/v1\/?$/, '')}${path}`;
  }
  return path;
}

const TOKEN_KEY = 'deepshield.token';
const USER_KEY = 'deepshield.user';

function readStoredToken() {
  const token = window.localStorage.getItem(TOKEN_KEY);
  if (token) return token;
  return window.sessionStorage.getItem(TOKEN_KEY);
}

function clearStoredAuth() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(USER_KEY);
}

function decodeJwtPayload(token) {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/');
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=');
    return JSON.parse(window.atob(padded));
  } catch {
    return null;
  }
}

function isJwtExpired(token) {
  const payload = decodeJwtPayload(token);
  if (!payload || typeof payload.exp !== 'number') return false;
  return payload.exp * 1000 <= Date.now();
}

let warmupPromise = null;

/**
 * Wake sleeping backends (HF cold starts) by probing health endpoints with backoff.
 * This is intentionally non-throwing for callers so UI can continue rendering.
 */
export async function warmupBackend({ attempts = 6, initialDelayMs = 1200 } = {}) {
  if (warmupPromise) return warmupPromise;

  warmupPromise = (async () => {
    let delay = initialDelayMs;

    for (let i = 0; i < attempts; i += 1) {
      try {
        const health = await api.get('/health', {
          timeout: 8000,
          validateStatus: () => true,
        });

        if (health.status === 200) {
          // Optional deeper check; keep best-effort and non-blocking.
          await api.get('/health/ready', { timeout: 10000, validateStatus: () => true });
          return true;
        }
      } catch (_e) {
        // Backend may still be waking up.
      }

      await new Promise((resolve) => setTimeout(resolve, delay));
      delay = Math.min(delay * 2, 10000);
    }

    return false;
  })();

  return warmupPromise;
}

api.interceptors.request.use((config) => {
  const token = readStoredToken();
  if (token && isJwtExpired(token)) {
    clearStoredAuth();
    return config;
  }
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) {
      clearStoredAuth();
    }
    const detail = err?.response?.data?.detail || err.message || 'Request failed';
    err.userMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
    return Promise.reject(err);
  }
);

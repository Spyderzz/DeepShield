import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 120000,
});

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
  const token = sessionStorage.getItem('deepshield.token');
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
      sessionStorage.removeItem('deepshield.token');
      sessionStorage.removeItem('deepshield.user');
      localStorage.removeItem('deepshield.token');
      localStorage.removeItem('deepshield.user');
    }
    const detail = err?.response?.data?.detail || err.message || 'Request failed';
    err.userMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
    return Promise.reject(err);
  }
);

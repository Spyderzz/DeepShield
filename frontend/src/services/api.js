import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 120000,
});

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

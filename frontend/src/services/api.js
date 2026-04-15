import axios from 'axios';

export const api = axios.create({
  baseURL: '/api/v1',
  timeout: 120000,
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const detail = err?.response?.data?.detail || err.message || 'Request failed';
    err.userMessage = typeof detail === 'string' ? detail : JSON.stringify(detail);
    return Promise.reject(err);
  }
);

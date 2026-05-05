import { api } from './api.js';

const TOKEN_KEY = 'deepshield.token';
const USER_KEY = 'deepshield.user';
export function getStoredToken() {
  return window.localStorage.getItem(TOKEN_KEY) || window.sessionStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = window.localStorage.getItem(USER_KEY) || window.sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function setAuth(token, user, remember = true) {
  clearAuth();
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
  window.sessionStorage.removeItem(TOKEN_KEY);
  window.sessionStorage.removeItem(USER_KEY);
}

export async function register(email, password, name) {
  const { data } = await api.post('/auth/register', { email, password, name: name || null });
  return data;
}

export async function login(email, password) {
  const { data } = await api.post('/auth/login', { email, password });
  return data;
}

export async function fetchMe() {
  const { data } = await api.get('/auth/me');
  return data;
}

export async function beginOAuth(provider, redirectTo = '/analyze', remember = true) {
  const { data } = await api.get(`/auth/oauth/${provider}/start`, {
    params: { redirect_to: redirectTo, remember: remember ? 1 : 0 },
  });
  return data;
}

import { api } from './api.js';

const TOKEN_KEY = 'deepshield.token';
const USER_KEY = 'deepshield.user';
const LEGACY_STORAGE = window.localStorage;
const STORAGE = window.sessionStorage;

export function clearLegacyAuth() {
  LEGACY_STORAGE.removeItem(TOKEN_KEY);
  LEGACY_STORAGE.removeItem(USER_KEY);
}

export function getStoredToken() {
  return STORAGE.getItem(TOKEN_KEY) || null;
}

export function getStoredUser() {
  const raw = STORAGE.getItem(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function setAuth(token, user) {
  clearLegacyAuth();
  STORAGE.setItem(TOKEN_KEY, token);
  STORAGE.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  STORAGE.removeItem(TOKEN_KEY);
  STORAGE.removeItem(USER_KEY);
  clearLegacyAuth();
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

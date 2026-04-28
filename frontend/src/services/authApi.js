import { api } from './api.js';

const TOKEN_KEY = 'deepshield.token';
const USER_KEY = 'deepshield.user';
const PRIMARY_STORAGE = window.localStorage;
const LEGACY_STORAGE = window.sessionStorage;

function migrateLegacyValue(key) {
  const current = PRIMARY_STORAGE.getItem(key);
  if (current) return current;
  const legacy = LEGACY_STORAGE.getItem(key);
  if (legacy) {
    PRIMARY_STORAGE.setItem(key, legacy);
    LEGACY_STORAGE.removeItem(key);
    return legacy;
  }
  return null;
}

export function clearLegacyAuth() {
  LEGACY_STORAGE.removeItem(TOKEN_KEY);
  LEGACY_STORAGE.removeItem(USER_KEY);
}

export function getStoredToken() {
  return migrateLegacyValue(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = migrateLegacyValue(USER_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

export function setAuth(token, user) {
  clearLegacyAuth();
  PRIMARY_STORAGE.setItem(TOKEN_KEY, token);
  PRIMARY_STORAGE.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  PRIMARY_STORAGE.removeItem(TOKEN_KEY);
  PRIMARY_STORAGE.removeItem(USER_KEY);
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

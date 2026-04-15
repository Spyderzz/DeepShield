import { createContext, useContext, useEffect, useState } from 'react';
import {
  clearAuth, getStoredToken, getStoredUser, setAuth,
  login as apiLogin, register as apiRegister, fetchMe,
} from '../services/authApi.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [token, setToken] = useState(() => getStoredToken());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (token && !user) {
      fetchMe().then(setUser).catch(() => { clearAuth(); setUser(null); setToken(null); });
    }
  }, [token, user]);

  const login = async (email, password) => {
    setLoading(true);
    try {
      const data = await apiLogin(email, password);
      setAuth(data.access_token, data.user);
      setToken(data.access_token);
      setUser(data.user);
      return data.user;
    } finally { setLoading(false); }
  };

  const register = async (email, password, name) => {
    setLoading(true);
    try {
      const data = await apiRegister(email, password, name);
      setAuth(data.access_token, data.user);
      setToken(data.access_token);
      setUser(data.user);
      return data.user;
    } finally { setLoading(false); }
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, isAuthed: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

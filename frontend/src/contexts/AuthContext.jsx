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
  // authReady=false only when a token exists but user needs async rehydration
  const [authReady, setAuthReady] = useState(() => {
    const t = getStoredToken();
    const u = getStoredUser();
    return !(t && !u);
  });

  useEffect(() => {
    if (token) {
      fetchMe()
        .then(setUser)
        .catch(() => { clearAuth(); setUser(null); setToken(null); })
        .finally(() => setAuthReady(true));
    } else {
      setAuthReady(true);
    }
  }, [token]);

  const login = async (email, password, remember = true) => {
    setLoading(true);
    try {
      const data = await apiLogin(email, password);
      setAuth(data.access_token, data.user, remember);
      setToken(data.access_token);
      setUser(data.user);
      setAuthReady(true);
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
      setAuthReady(true);
      return data.user;
    } finally { setLoading(false); }
  };

  const logout = () => {
    clearAuth();
    setUser(null);
    setToken(null);
    setAuthReady(true);
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, authReady, login, register, logout, isAuthed: !!token && !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}

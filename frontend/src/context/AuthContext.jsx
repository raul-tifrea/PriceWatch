import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';
const AuthContext = createContext(null);
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('pw_token'));
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('pw_token');
          setToken(null);
          delete api.defaults.headers.common['Authorization'];
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);
  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, email: userEmail } = res.data;
    localStorage.setItem('pw_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setToken(access_token);
    setUser({ email: userEmail });
    window.postMessage({ type: 'PRICEWATCH_LOGIN', token: access_token, email: userEmail }, '*');
    return res.data;
  };
  const register = async (email, password) => {
    const res = await api.post('/auth/register', { email, password });
    const { access_token, email: userEmail } = res.data;
    localStorage.setItem('pw_token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    setToken(access_token);
    setUser({ email: userEmail });
    window.postMessage({ type: 'PRICEWATCH_LOGIN', token: access_token, email: userEmail }, '*');
    return res.data;
  };
  const logout = () => {
    localStorage.removeItem('pw_token');
    delete api.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
    window.postMessage({ type: 'PRICEWATCH_LOGOUT' }, '*');
  };
  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  return useContext(AuthContext);
}
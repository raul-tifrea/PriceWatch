import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import { Activity, PlusCircle, Sun, Moon, LogOut, User } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import Dashboard from './pages/Dashboard';
import AddProduct from './pages/AddProduct';
import Login from './pages/Login';
import './index.css';
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  return user ? children : <Navigate to="/login" replace />;
}
function AppShell() {
  const { user, logout, loading } = useAuth();
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  if (loading) return null;
  if (!user) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }
  return (
    <div className="app-container">
      <header className="header">
        <Link to="/" style={{ textDecoration: 'none' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity color="var(--primary-color)" size={32} />
            <h1 className="header-title" style={{ marginBottom: 0 }}>PriceWatch</h1>
          </div>
        </Link>
        <nav className="header-nav" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div className="user-badge">
            <User size={14} />
            <span className="user-badge-email">{user.email}</span>
          </div>
          <button
            onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
            className="btn btn-outline"
            style={{ padding: '0.4rem', border: 'none' }}
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          <Link to="/add" className="btn btn-primary">
            <PlusCircle size={18} />
            Add Product
          </Link>
          <button
            onClick={logout}
            className="btn btn-outline"
            style={{ padding: '0.4rem 0.8rem', display: 'flex', gap: '0.4rem', alignItems: 'center', fontSize: '0.85rem' }}
            title="Log out"
          >
            <LogOut size={16} />
            Log out
          </button>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/add" element={<AddProduct />} />
          <Route path="/login" element={<Navigate to="/" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
function App() {
  return (
    <AuthProvider>
      <Router>
        <AppShell />
      </Router>
    </AuthProvider>
  );
}
export default App;
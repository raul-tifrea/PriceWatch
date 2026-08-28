import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Activity, PlusCircle, Sun, Moon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import AddProduct from './pages/AddProduct';
import './index.css';

function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return (
    <Router>
      <div className="app-container">
        <header className="header">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity color="var(--primary-color)" size={32} />
              <h1 className="header-title" style={{ marginBottom: 0 }}>PriceWatch</h1>
            </div>
          </Link>
          <nav className="header-nav" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <button 
              onClick={toggleTheme} 
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
          </nav>
        </header>
        
        <main>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/add" element={<AddProduct />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

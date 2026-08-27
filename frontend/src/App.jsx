import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Activity, PlusCircle } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import AddProduct from './pages/AddProduct';
import './index.css';

function App() {
  return (
    <Router>
      <div className="app-container">
        <header className="header">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Activity color="#58a6ff" size={32} />
              <h1 className="header-title" style={{ marginBottom: 0 }}>PriceWatch</h1>
            </div>
          </Link>
          <nav className="header-nav">
            <Link to="/" className="btn btn-outline">Dashboard</Link>
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

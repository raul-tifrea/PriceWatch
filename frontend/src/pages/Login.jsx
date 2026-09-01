import React, { useState } from 'react';
import { Activity } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
export default function Login() {
  const { login, register } = useAuth();
  const [tab, setTab] = useState('login'); 
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (tab === 'login') {
        await login(email, password);
      } else {
        await register(email, password);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong. Try again.');
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="auth-page">
      {}
      <div className="auth-orb auth-orb--1" />
      <div className="auth-orb auth-orb--2" />
      <div className="auth-orb auth-orb--3" />
      <div className="auth-card">
        {}
        <div className="auth-logo">
          <div className="auth-logo-icon">
            <Activity size={28} color="#22c55e" />
          </div>
          <span className="auth-logo-text">PriceWatch</span>
        </div>
        <h2 className="auth-title">
          {tab === 'login' ? 'Welcome back' : 'Create your account'}
        </h2>
        <p className="auth-subtitle">
          {tab === 'login'
            ? 'Track prices smarter. Log in to your dashboard.'
            : 'Start tracking product prices across Romania.'}
        </p>
        {}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${tab === 'login' ? 'auth-tab--active' : ''}`}
            onClick={() => { setTab('login'); setError(''); }}
            type="button"
          >
            Log In
          </button>
          <button
            className={`auth-tab ${tab === 'register' ? 'auth-tab--active' : ''}`}
            onClick={() => { setTab('register'); setError(''); }}
            type="button"
          >
            Sign Up
          </button>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-email">Email address</label>
            <input
              id="auth-email"
              className="auth-input"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="auth-field">
            <label className="auth-label" htmlFor="auth-password">Password</label>
            <input
              id="auth-password"
              className="auth-input"
              type="password"
              placeholder={tab === 'register' ? 'At least 6 characters' : '••••••••'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <div className="auth-error">{error}</div>}
          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >
            {loading
              ? (tab === 'login' ? 'Signing in…' : 'Creating account…')
              : (tab === 'login' ? 'Sign In' : 'Create Account')}
          </button>
        </form>
        <p className="auth-footer">
          {tab === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            className="auth-footer-link"
            onClick={() => { setTab(tab === 'login' ? 'register' : 'login'); setError(''); }}
          >
            {tab === 'login' ? 'Sign up' : 'Log in'}
          </button>
        </p>
      </div>
    </div>
  );
}
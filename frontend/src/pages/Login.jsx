import React, { useState } from 'react';
import { useNavigate, Navigate, Link } from 'react-router-dom';
import { Shield, Lock, Mail, ArrowRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import ErrorMessage from '../components/ErrorMessage';

export const Login = () => {
  const { login, isAuthenticated, isLoading: isAuthLoading } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isAuthLoading && isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    setIsSubmitting(true);

    try {
      await login(email.trim(), password.trim());
      navigate('/dashboard', { replace: true });
    } catch (err) {
      console.error('Login error:', err);
      if (err.response?.status === 404) {
        setError('Backend API route not found. Ensure Flask backend is running on http://localhost:5000.');
      } else if (err.response?.status === 401) {
        setError(err.response?.data?.message || 'Invalid email or password');
      } else {
        const message = err.response?.data?.message || err.response?.data?.error || err.message || 'Authentication failed';
        setError(message);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-wrapper">
      <div className="login-card">
        <div className="login-header">
          <div className="login-brand-icon">
            <Shield size={28} />
          </div>
          <h1 className="login-title">Monitoring Platform</h1>
          <p className="login-subtitle">Sign in to access real-time telemetry dashboard</p>
        </div>

        <ErrorMessage message={error} />

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="email">Email Address</label>
            <div className="search-input-wrapper">
              <Mail size={18} />
              <input
                id="email"
                type="email"
                className="form-control"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="password">Password</label>
            <div className="search-input-wrapper">
              <Lock size={18} />
              <input
                id="password"
                type="password"
                className="form-control"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '0.75rem', padding: '0.75rem' }}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span>Authenticating...</span>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <div style={{ marginTop: '1.25rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--primary-color)', fontWeight: 600, textDecoration: 'none' }}>
            Register Now
          </Link>
        </div>

        <div style={{ marginTop: '1.5rem', paddingTop: '1.25rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-dim)', textAlign: 'center' }}>
          <p style={{ fontWeight: 500, color: 'var(--text-muted)' }}>Demo Seed Credentials:</p>
          <p style={{ marginTop: '0.25rem' }}>Admin: <code>admin@example.com</code> | <code>admin123</code></p>
          <p>Operator: <code>operator@example.com</code> | <code>operator123</code></p>
          <p>Viewer: <code>viewer@example.com</code> | <code>viewer123</code></p>
        </div>
      </div>
    </div>
  );
};

export default Login;

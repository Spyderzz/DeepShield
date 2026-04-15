import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AuthForm from '../components/auth/AuthForm.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function LoginPage() {
  const { login, loading, isAuthed } = useAuth();
  const [error, setError] = useState(null);
  const nav = useNavigate();
  const loc = useLocation();
  const redirectTo = loc.state?.from || '/history';

  if (isAuthed) {
    nav(redirectTo, { replace: true });
    return null;
  }

  const handle = async ({ email, password }) => {
    setError(null);
    try {
      await login(email, password);
      nav(redirectTo, { replace: true });
    } catch (err) {
      setError(err.userMessage || err.message || 'Login failed');
    }
  };

  return (
    <section style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <h2>Log in</h2>
      <AuthForm mode="login" onSubmit={handle} loading={loading} error={error} />
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
        No account? <Link to="/register" style={{ color: 'var(--color-primary-600)' }}>Register here</Link>.
      </p>
    </section>
  );
}

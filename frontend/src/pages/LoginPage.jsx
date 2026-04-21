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
    <section
      style={{
        minHeight: '72vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `
          radial-gradient(ellipse at 20% 30%, rgba(30, 136, 229, 0.20) 0px, transparent 55%),
          radial-gradient(ellipse at 80% 70%, rgba(139, 92, 246, 0.16) 0px, transparent 55%),
          radial-gradient(ellipse at 55% 90%, rgba(16, 185, 129, 0.10) 0px, transparent 50%)
        `,
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--space-8)',
      }}
    >
      <div
        className="glass-panel"
        style={{ padding: 'var(--space-8)', maxWidth: 420, width: '100%' }}
      >
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-6)' }}>
          <h2 style={{ margin: 0, marginBottom: 'var(--space-2)' }}>Welcome back</h2>
          <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Sign in to access your analysis history
          </p>
        </div>
        <AuthForm mode="login" onSubmit={handle} loading={loading} error={error} />
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          textAlign: 'center',
          marginTop: 'var(--space-4)',
          marginBottom: 0,
        }}>
          No account?{' '}
          <Link to="/register" style={{ color: 'var(--color-primary-600)', fontWeight: 'var(--font-weight-medium)' }}>
            Register here
          </Link>
        </p>
      </div>
    </section>
  );
}

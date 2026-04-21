import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import AuthForm from '../components/auth/AuthForm.jsx';
import { useAuth } from '../contexts/AuthContext.jsx';

export default function RegisterPage() {
  const { register, loading, isAuthed } = useAuth();
  const [error, setError] = useState(null);
  const nav = useNavigate();

  if (isAuthed) {
    nav('/history', { replace: true });
    return null;
  }

  const handle = async ({ email, password, name }) => {
    setError(null);
    try {
      await register(email, password, name);
      nav('/history', { replace: true });
    } catch (err) {
      setError(err.userMessage || err.message || 'Registration failed');
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
          radial-gradient(ellipse at 75% 20%, rgba(30, 136, 229, 0.18) 0px, transparent 55%),
          radial-gradient(ellipse at 20% 75%, rgba(139, 92, 246, 0.15) 0px, transparent 55%),
          radial-gradient(ellipse at 50% 50%, rgba(99, 102, 241, 0.08) 0px, transparent 60%)
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
          <h2 style={{ margin: 0, marginBottom: 'var(--space-2)' }}>Create account</h2>
          <p style={{ margin: 0, fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Join DeepShield to save and revisit your analyses
          </p>
        </div>
        <AuthForm mode="register" onSubmit={handle} loading={loading} error={error} />
        <p style={{
          fontSize: 'var(--font-size-sm)',
          color: 'var(--color-text-secondary)',
          textAlign: 'center',
          marginTop: 'var(--space-4)',
          marginBottom: 0,
        }}>
          Already registered?{' '}
          <Link to="/login" style={{ color: 'var(--color-primary-600)', fontWeight: 'var(--font-weight-medium)' }}>
            Log in
          </Link>
        </p>
      </div>
    </section>
  );
}

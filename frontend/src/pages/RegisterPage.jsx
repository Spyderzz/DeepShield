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
    <section style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <h2>Create account</h2>
      <AuthForm mode="register" onSubmit={handle} loading={loading} error={error} />
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
        Already registered? <Link to="/login" style={{ color: 'var(--color-primary-600)' }}>Log in</Link>.
      </p>
    </section>
  );
}

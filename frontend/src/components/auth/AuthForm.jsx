import { useState } from 'react';

const inputStyle = {
  padding: 'var(--space-3)',
  border: '1px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--font-size-base)',
  background: 'var(--color-surface)',
  color: 'var(--color-text-primary)',
};

export default function AuthForm({ mode, onSubmit, loading, error }) {
  const isRegister = mode === 'register';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');

  const handle = (e) => {
    e.preventDefault();
    onSubmit({ email: email.trim(), password, name: name.trim() });
  };

  return (
    <form onSubmit={handle} style={{ display: 'grid', gap: 'var(--space-3)', maxWidth: 420 }}>
      {isRegister && (
        <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
          <span style={{ fontSize: 'var(--font-size-sm)' }}>Name (optional)</span>
          <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
        </label>
      )}
      <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)' }}>Email</span>
        <input type="email" required style={inputStyle} value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
      </label>
      <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)' }}>Password</span>
        <input type="password" required minLength={6} style={inputStyle} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={isRegister ? 'new-password' : 'current-password'} />
      </label>
      {error && (
        <div style={{ color: 'var(--color-danger)', background: '#FFEBEE', padding: 'var(--space-2) var(--space-3)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)' }}>
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: 'var(--space-3) var(--space-6)',
          background: loading ? 'var(--color-border)' : 'var(--color-primary-500)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: loading ? 'wait' : 'pointer',
          fontWeight: 'var(--font-weight-semibold)',
        }}
      >
        {loading ? (isRegister ? 'Creating account…' : 'Logging in…') : (isRegister ? 'Create account' : 'Log in')}
      </button>
    </form>
  );
}

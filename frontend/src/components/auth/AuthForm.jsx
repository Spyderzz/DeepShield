import { useState } from 'react';

const inputStyle = {
  padding: 'var(--space-3) var(--space-4)',
  border: '1.5px solid var(--color-border)',
  borderRadius: 'var(--radius-md)',
  fontSize: 'var(--font-size-base)',
  background: 'rgba(255, 255, 255, 0.80)',
  color: 'var(--color-text-primary)',
  width: '100%',
  boxSizing: 'border-box',
  transition: 'border-color 0.2s, box-shadow 0.2s',
  outline: 'none',
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
    <form onSubmit={handle} style={{ display: 'grid', gap: 'var(--space-4)' }}>
      {isRegister && (
        <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)' }}>
            Name (optional)
          </span>
          <input
            style={inputStyle}
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoComplete="name"
            placeholder="Your name"
          />
        </label>
      )}
      <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)' }}>
          Email
        </span>
        <input
          type="email"
          required
          style={inputStyle}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          placeholder="you@example.com"
        />
      </label>
      <label style={{ display: 'grid', gap: 'var(--space-1)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-secondary)' }}>
          Password
        </span>
        <input
          type="password"
          required
          minLength={6}
          style={inputStyle}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete={isRegister ? 'new-password' : 'current-password'}
          placeholder="••••••••"
        />
      </label>
      {error && (
        <div style={{
          color: 'var(--color-danger)',
          background: '#FFEBEE',
          padding: 'var(--space-2) var(--space-3)',
          borderRadius: 'var(--radius-md)',
          fontSize: 'var(--font-size-sm)',
        }}>
          {error}
        </div>
      )}
      <button
        type="submit"
        disabled={loading}
        style={{
          padding: 'var(--space-3) var(--space-6)',
          background: loading
            ? 'var(--color-border)'
            : 'linear-gradient(135deg, var(--color-primary-500) 0%, var(--color-primary-600) 100%)',
          color: 'white',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          cursor: loading ? 'wait' : 'pointer',
          fontWeight: 'var(--font-weight-semibold)',
          fontSize: 'var(--font-size-base)',
          boxShadow: loading ? 'none' : '0 4px 14px rgba(30,136,229,0.28)',
          transition: 'background 0.2s, box-shadow 0.2s',
          width: '100%',
          marginTop: 'var(--space-1)',
        }}
      >
        {loading
          ? (isRegister ? 'Creating account…' : 'Logging in…')
          : (isRegister ? 'Create account' : 'Log in')}
      </button>
    </form>
  );
}

import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext.jsx';

const linkStyle = ({ isActive }) => ({
  color: isActive ? 'var(--color-primary-600)' : 'var(--color-text-secondary)',
  fontWeight: isActive ? 'var(--font-weight-semibold)' : 'var(--font-weight-medium)',
  textDecoration: 'none',
  padding: 'var(--space-2) var(--space-3)',
});

export default function Navbar() {
  const { user, isAuthed, logout } = useAuth();
  const nav = useNavigate();

  const handleLogout = () => {
    logout();
    nav('/', { replace: true });
  };

  return (
    <nav
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: 'var(--space-4) var(--space-8)',
        background: 'var(--color-surface)',
        borderBottom: '1px solid var(--color-border)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <NavLink to="/" style={{ fontWeight: 'var(--font-weight-bold)', fontSize: 'var(--font-size-xl)', color: 'var(--color-primary-600)' }}>
        DeepShield
      </NavLink>
      <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
        <NavLink to="/analyze" style={linkStyle}>Analyze</NavLink>
        <NavLink to="/history" style={linkStyle}>History</NavLink>
        <NavLink to="/about" style={linkStyle}>About</NavLink>
        {isAuthed ? (
          <>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', padding: 'var(--space-2) var(--space-3)' }}>
              {user?.name || user?.email}
            </span>
            <button
              onClick={handleLogout}
              style={{
                padding: 'var(--space-2) var(--space-3)',
                background: 'transparent',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                color: 'var(--color-text-secondary)',
                fontSize: 'var(--font-size-sm)',
              }}
            >Logout</button>
          </>
        ) : (
          <>
            <NavLink to="/login" style={linkStyle}>Login</NavLink>
            <NavLink to="/register" style={linkStyle}>Register</NavLink>
          </>
        )}
      </div>
    </nav>
  );
}

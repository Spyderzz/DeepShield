import { NavLink } from 'react-router-dom';

const linkStyle = ({ isActive }) => ({
  color: isActive ? 'var(--color-primary-600)' : 'var(--color-text-secondary)',
  fontWeight: isActive ? 'var(--font-weight-semibold)' : 'var(--font-weight-medium)',
  textDecoration: 'none',
  padding: 'var(--space-2) var(--space-3)',
});

export default function Navbar() {
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
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        <NavLink to="/analyze" style={linkStyle}>Analyze</NavLink>
        <NavLink to="/history" style={linkStyle}>History</NavLink>
        <NavLink to="/about" style={linkStyle}>About</NavLink>
        <NavLink to="/login" style={linkStyle}>Login</NavLink>
      </div>
    </nav>
  );
}

import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <section style={{ textAlign: 'center', padding: 'var(--space-16) 0' }}>
      <h1>404</h1>
      <p style={{ color: 'var(--color-text-secondary)' }}>The page you're looking for doesn't exist.</p>
      <Link to="/">Return home →</Link>
    </section>
  );
}

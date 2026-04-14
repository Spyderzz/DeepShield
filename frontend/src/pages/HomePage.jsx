import { Link } from 'react-router-dom';

export default function HomePage() {
  return (
    <section>
      <h1>Detect misinformation with explainable AI</h1>
      <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-lg)' }}>
        Upload an image, video, news article, or screenshot. DeepShield returns authenticity verdicts backed by transparency signals and trusted sources.
      </p>
      <Link
        to="/analyze"
        style={{
          display: 'inline-block',
          marginTop: 'var(--space-6)',
          padding: 'var(--space-3) var(--space-6)',
          background: 'var(--color-primary-500)',
          color: 'white',
          borderRadius: 'var(--radius-md)',
          fontWeight: 'var(--font-weight-semibold)',
          boxShadow: 'var(--shadow-md)',
        }}
      >
        Start Analysis →
      </Link>
    </section>
  );
}

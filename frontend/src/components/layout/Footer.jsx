export default function Footer() {
  return (
    <footer
      style={{
        padding: 'var(--space-6) var(--space-8)',
        background: 'var(--color-surface)',
        borderTop: '1px solid var(--color-border)',
        color: 'var(--color-text-secondary)',
        fontSize: 'var(--font-size-sm)',
        textAlign: 'center',
      }}
    >
      © {new Date().getFullYear()} DeepShield — Explainable AI misinformation detection.
    </footer>
  );
}

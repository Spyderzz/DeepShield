export default function ContradictionPanel({ items = [] }) {
  if (!items.length) return null;
  return (
    <div style={{
      display: 'grid',
      gap: 'var(--space-3)',
      padding: 'var(--space-4)',
      background: '#FFF4F4',
      border: '1px solid #FFC9C9',
      borderRadius: 'var(--radius-md)',
    }}>
      <h4 style={{ margin: 0, color: '#C62828', fontWeight: 'var(--font-weight-semibold)' }}>
        ⚠ Contradicting Evidence — Fact-Checks ({items.length})
      </h4>
      <div style={{ fontSize: 'var(--font-size-sm)', color: '#8B3A3A' }}>
        Fact-checkers have published articles potentially disputing related claims. Review before sharing.
      </div>
      {items.map((it, i) => (
        <a
          key={it.url || i}
          href={it.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'block',
            padding: 'var(--space-3)',
            background: 'white',
            border: '1px solid #FFC9C9',
            borderRadius: 'var(--radius-md)',
            textDecoration: 'none',
            color: 'inherit',
          }}
        >
          <div style={{
            fontWeight: 'var(--font-weight-medium)',
            color: 'var(--color-text-primary)',
          }}>
            {it.title || 'Untitled fact-check'}
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            marginTop: 2,
          }}>
            {it.source_name} · <span style={{ color: '#C62828', fontWeight: 'var(--font-weight-medium)' }}>{it.type || 'fact_check'}</span>
          </div>
        </a>
      ))}
    </div>
  );
}

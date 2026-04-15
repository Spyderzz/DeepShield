import SourceCard from './SourceCard.jsx';

export default function SourcePanel({ sources = [] }) {
  if (!sources.length) return null;
  return (
    <div style={{ display: 'grid', gap: 'var(--space-3)' }}>
      <h4 style={{ margin: 0, fontWeight: 'var(--font-weight-semibold)' }}>
        Trusted Source Cross-Reference ({sources.length})
      </h4>
      {sources.map((src, i) => (
        <SourceCard key={src.url || i} source={src} />
      ))}
    </div>
  );
}

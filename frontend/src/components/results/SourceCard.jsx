import { formatDateIST } from '../../utils/dateTime.js';

export default function SourceCard({ source }) {
  const trusted = source.relevance_score >= 0.9;
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      style={{
        display: 'block',
        padding: 'var(--space-3)',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        textDecoration: 'none',
        color: 'inherit',
        transition: 'border-color 0.2s, box-shadow 0.2s',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-primary-300)'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.boxShadow = 'none'; }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-2)' }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontWeight: 'var(--font-weight-medium)',
            color: 'var(--color-text-primary)',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {source.title || 'Untitled'}
          </div>
          <div style={{
            fontSize: 'var(--font-size-xs)',
            color: 'var(--color-text-secondary)',
            marginTop: 2,
          }}>
            {source.source_name}
            {source.published_at && ` · ${formatDateIST(source.published_at)}`}
            {typeof source.relevance_score === 'number' && ` · relevance ${(source.relevance_score * 100).toFixed(0)}%`}
          </div>
        </div>
        <div style={{
          fontSize: 'var(--font-size-xs)',
          padding: '2px 8px',
          borderRadius: 'var(--radius-sm)',
          background: trusted ? 'rgba(67,160,71,0.1)' : 'rgba(66,165,245,0.1)',
          color: trusted ? '#43A047' : '#42A5F5',
          fontWeight: 'var(--font-weight-medium)',
          whiteSpace: 'nowrap',
        }}>
          {trusted ? '★ Trusted' : 'Relevant'}
        </div>
      </div>
    </a>
  );
}

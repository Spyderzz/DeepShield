import { SEVERITY_COLORS } from '../../utils/constants.js';

export default function VerdictCard({ verdict, mediaType, timestamp }) {
  const color = SEVERITY_COLORS[verdict.severity] || 'var(--color-text-secondary)';
  return (
    <div
      style={{
        background: 'var(--color-surface)',
        borderLeft: `4px solid ${color}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-6)',
        boxShadow: 'var(--shadow-sm)',
      }}
    >
      <div style={{ fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', letterSpacing: 1, color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
        Verdict
      </div>
      <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 'var(--font-weight-bold)', color }}>
        {verdict.label}
      </div>
      <div style={{ marginTop: 'var(--space-4)', display: 'grid', gap: 'var(--space-2)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
        <div>Model confidence: <b style={{ color: 'var(--color-text-primary)' }}>{(verdict.model_confidence * 100).toFixed(1)}%</b></div>
        <div>Model label: <b style={{ color: 'var(--color-text-primary)' }}>{verdict.model_label}</b></div>
        <div>Media type: <b style={{ color: 'var(--color-text-primary)' }}>{mediaType}</b></div>
        <div>Processed: <b style={{ color: 'var(--color-text-primary)' }}>{new Date(timestamp).toLocaleString()}</b></div>
      </div>
    </div>
  );
}

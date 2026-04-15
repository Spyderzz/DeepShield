const SEV = {
  high: { color: '#C62828', bg: '#FFEBEE', label: 'HIGH' },
  medium: { color: '#EF6C00', bg: '#FFF3E0', label: 'MEDIUM' },
  low: { color: '#2E7D32', bg: '#E8F5E9', label: 'LOW' },
};

const TYPE_LABEL = {
  gan_artifact: 'GAN / diffusion artifact',
  facial_boundary: 'Facial boundary',
  compression: 'Compression anomaly',
  lighting: 'Lighting inconsistency',
};

export default function IndicatorCards({ indicators = [] }) {
  if (!indicators.length) {
    return (
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
        No artifact indicators available.
      </div>
    );
  }
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 'var(--space-4)' }}>
      {indicators.map((ind, i) => {
        const sev = SEV[ind.severity] || SEV.low;
        return (
          <div
            key={i}
            style={{
              background: 'var(--color-surface)',
              borderLeft: `4px solid ${sev.color}`,
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              boxShadow: 'var(--shadow-sm)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
              <span style={{ fontWeight: 'var(--font-weight-semibold)' }}>{TYPE_LABEL[ind.type] || ind.type}</span>
              <span style={{ fontSize: 'var(--font-size-xs)', padding: '2px 8px', borderRadius: 'var(--radius-full)', background: sev.bg, color: sev.color, fontWeight: 'var(--font-weight-semibold)' }}>
                {sev.label}
              </span>
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
              {ind.description}
            </div>
            <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
              confidence {(ind.confidence * 100).toFixed(0)}%
            </div>
          </div>
        );
      })}
    </div>
  );
}

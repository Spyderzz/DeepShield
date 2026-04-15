import { scoreColor } from '../../utils/constants.js';

export default function FrameTimeline({ frames = [] }) {
  if (!frames.length) {
    return (
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
        No frames sampled.
      </div>
    );
  }

  const maxT = Math.max(...frames.map((f) => f.timestamp_s), 1);

  return (
    <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
      <div
        style={{
          position: 'relative',
          height: 48,
          background: 'var(--color-surface-alt, #F5F5F5)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--color-border)',
          overflow: 'hidden',
        }}
      >
        {frames.map((f, i) => {
          const left = `${(f.timestamp_s / maxT) * 100}%`;
          const authScore = Math.round((1 - f.suspicious_prob) * 100);
          const color = f.has_face ? scoreColor(authScore) : '#BDBDBD';
          const faceTag = f.has_face ? 'face' : 'no face';
          return (
            <div
              key={i}
              title={`t=${f.timestamp_s.toFixed(2)}s · ${faceTag} · ${f.label} (${(f.confidence * 100).toFixed(0)}%) · suspicious ${(f.suspicious_prob * 100).toFixed(0)}%`}
              style={{
                position: 'absolute',
                left,
                top: 4,
                width: 8,
                height: 40,
                borderRadius: 2,
                background: color,
                opacity: f.has_face ? 1 : 0.45,
                transform: 'translateX(-4px)',
                boxShadow: f.is_suspicious ? '0 0 0 2px rgba(198, 40, 40, 0.35)' : 'none',
                cursor: 'help',
              }}
            />
          );
        })}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)' }}>
        <span>0.0 s</span>
        <span>{maxT.toFixed(1)} s</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 'var(--space-2)' }}>
        {frames.map((f, i) => (
          <div
            key={i}
            style={{
              padding: 'var(--space-2) var(--space-3)',
              background: f.has_face ? 'var(--color-surface)' : '#FAFAFA',
              border: `1px solid ${f.is_suspicious ? '#EF9A9A' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-sm, 4px)',
              fontSize: 'var(--font-size-xs)',
              opacity: f.has_face ? 1 : 0.7,
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 'var(--font-weight-semibold)' }}>t = {f.timestamp_s.toFixed(2)}s</span>
              <span style={{ fontSize: 10, padding: '1px 6px', borderRadius: 999, background: f.has_face ? '#E8F5E9' : '#EEEEEE', color: f.has_face ? '#2E7D32' : '#757575' }}>
                {f.has_face ? 'face' : 'no face'}
              </span>
            </div>
            <div style={{ color: 'var(--color-text-secondary)' }}>
              {f.label} · {(f.confidence * 100).toFixed(0)}%
            </div>
            {f.has_face ? (
              <div style={{ color: f.is_suspicious ? 'var(--color-danger)' : 'var(--color-text-secondary)' }}>
                suspicious {(f.suspicious_prob * 100).toFixed(0)}%
              </div>
            ) : (
              <div style={{ color: 'var(--color-text-disabled)', fontStyle: 'italic' }}>excluded from score</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

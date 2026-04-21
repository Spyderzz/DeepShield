function MetricRow({ label, value, badge }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: '1px solid var(--color-border)' }}>
      <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>{label}</span>
      <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-semibold)', color: badge }}>{value}</span>
    </div>
  );
}

function ScoreBar({ score }) {
  const pct = Math.max(0, Math.min(100, score));
  const color = pct >= 70 ? 'var(--color-success, #22c55e)' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div style={{ marginBottom: 'var(--space-4)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Audio Authenticity Score</span>
        <span style={{ fontWeight: 'var(--font-weight-bold)', color, fontSize: 'var(--font-size-lg)' }}>{Math.round(pct)}</span>
      </div>
      <div style={{ height: 8, background: 'var(--color-border)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 4, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  );
}

export default function AudioCard({ audio }) {
  if (!audio) return null;

  if (!audio.has_audio) {
    return (
      <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
        <h3 style={{ marginTop: 0 }}>Audio Analysis</h3>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)', margin: 0 }}>
          No audio track detected in this video — audio deepfake analysis skipped.
        </p>
      </div>
    );
  }

  const spec = audio.spectral_variance;
  const specLabel = spec < 0.1 ? 'Low (AI-typical)' : spec < 0.3 ? 'Moderate' : 'High (natural)';
  const specColor = spec < 0.1 ? '#ef4444' : spec < 0.3 ? '#f59e0b' : 'var(--color-success, #22c55e)';

  const silLabel = audio.silence_ratio < 0.05
    ? 'Very low (suspicious)'
    : audio.silence_ratio > 0.8 ? 'Very high' : 'Normal';
  const silColor = audio.silence_ratio < 0.05 ? '#ef4444' : 'var(--color-text-primary)';

  const rmsLabel = audio.rms_consistency > 0.92 ? 'Unnaturally even' : 'Natural variation';
  const rmsColor = audio.rms_consistency > 0.92 ? '#f59e0b' : 'var(--color-text-primary)';

  return (
    <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
      <h3 style={{ marginTop: 0 }}>Audio Deepfake Analysis</h3>
      <ScoreBar score={audio.audio_authenticity_score} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-2)' }}>
        <MetricRow label="Duration" value={`${audio.duration_s}s`} badge="var(--color-text-primary)" />
        <MetricRow label="Silence ratio" value={silLabel} badge={silColor} />
        <MetricRow label="Spectral variance" value={specLabel} badge={specColor} />
        <MetricRow label="RMS consistency" value={rmsLabel} badge={rmsColor} />
      </div>
      <p style={{ marginTop: 'var(--space-3)', marginBottom: 0, fontSize: 'var(--font-size-xs, 11px)', color: 'var(--color-text-secondary)' }}>
        Analysis uses signal-processing heuristics (spectral centroid variance, silence ratio, RMS consistency). A trained ASVspoof model would improve accuracy.
      </p>
    </div>
  );
}

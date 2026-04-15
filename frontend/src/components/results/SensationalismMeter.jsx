const LEVEL_CONFIG = {
  Low:    { color: '#43A047', emoji: '✅', bg: 'rgba(67, 160, 71, 0.08)' },
  Medium: { color: '#FFA726', emoji: '⚠️', bg: 'rgba(255, 167, 38, 0.08)' },
  High:   { color: '#E53935', emoji: '🚨', bg: 'rgba(229, 57, 53, 0.08)' },
};

export default function SensationalismMeter({ sensationalism }) {
  if (!sensationalism) return null;
  const { score, level, exclamation_count, caps_word_count, clickbait_matches, emotional_word_count, superlative_count } = sensationalism;
  const cfg = LEVEL_CONFIG[level] || LEVEL_CONFIG.Low;

  const signals = [
    { label: 'Exclamation marks', value: exclamation_count },
    { label: 'ALL CAPS words', value: caps_word_count },
    { label: 'Clickbait patterns', value: clickbait_matches },
    { label: 'Emotional words', value: emotional_word_count },
    { label: 'Superlatives', value: superlative_count },
  ].filter(s => s.value > 0);

  return (
    <div style={{
      padding: 'var(--space-4)',
      background: cfg.bg,
      border: `1px solid ${cfg.color}33`,
      borderRadius: 'var(--radius-md)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        <span style={{ fontSize: '1.4rem' }}>{cfg.emoji}</span>
        <div>
          <div style={{ fontWeight: 'var(--font-weight-semibold)', color: 'var(--color-text-primary)' }}>
            Sensationalism: {level}
          </div>
          <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
            Score: {score}/100
          </div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{
        height: 6,
        background: 'var(--color-border)',
        borderRadius: 3,
        overflow: 'hidden',
        marginBottom: signals.length ? 'var(--space-3)' : 0,
      }}>
        <div style={{
          width: `${score}%`,
          height: '100%',
          background: cfg.color,
          borderRadius: 3,
          transition: 'width 0.6s ease',
        }} />
      </div>

      {/* Signal breakdown */}
      {signals.length > 0 && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 'var(--space-2)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-secondary)',
        }}>
          {signals.map(s => (
            <span key={s.label} style={{
              padding: '2px 8px',
              background: 'rgba(255,255,255,0.5)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
            }}>
              {s.label}: {s.value}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

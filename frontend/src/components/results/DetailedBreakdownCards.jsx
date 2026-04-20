import { useState } from 'react';

const COMPONENTS = [
  { key: 'facial_symmetry',      label: 'Facial Symmetry',         icon: '👤' },
  { key: 'skin_texture',         label: 'Skin Texture',            icon: '🔬' },
  { key: 'lighting_consistency', label: 'Lighting Consistency',    icon: '💡' },
  { key: 'background_coherence', label: 'Background Coherence',    icon: '🖼️' },
  { key: 'anatomy_hands_eyes',   label: 'Anatomy & Hands / Eyes',  icon: '✋' },
  { key: 'context_objects',      label: 'Context & Objects',       icon: '📦' },
];

function scoreColor(score) {
  if (score >= 70) return '#43A047';
  if (score >= 40) return '#FB8C00';
  return '#E53935';
}

function ComponentCard({ icon, label, data }) {
  const [expanded, setExpanded] = useState(false);
  const score = data?.score ?? 75;
  const notes = data?.notes || '';
  const color = scoreColor(score);

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => setExpanded(e => !e)}
      onKeyDown={e => e.key === 'Enter' && setExpanded(v => !v)}
      style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        cursor: 'pointer',
        userSelect: 'none',
        outline: 'none',
        transition: 'box-shadow 0.15s',
      }}
      onFocus={e => (e.currentTarget.style.boxShadow = '0 0 0 2px var(--color-primary-300, #A5B4FC)')}
      onBlur={e => (e.currentTarget.style.boxShadow = '')}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
          {icon} {label}
        </span>
        <span style={{ fontSize: 'var(--font-size-base)', fontWeight: 'var(--font-weight-bold)', color }}>
          {score}%
        </span>
      </div>

      {/* score bar */}
      <div style={{ background: '#E5E7EB', borderRadius: 4, height: 5, overflow: 'hidden' }}>
        <div style={{
          width: `${score}%`,
          height: '100%',
          background: color,
          borderRadius: 4,
          transition: 'width 0.5s ease',
        }} />
      </div>

      {/* notes */}
      {expanded && notes && (
        <div style={{
          marginTop: 'var(--space-2)',
          fontSize: 'var(--font-size-xs)',
          color: 'var(--color-text-secondary)',
          lineHeight: 1.5,
        }}>
          {notes}
        </div>
      )}
      {!expanded && notes && (
        <div style={{ marginTop: 3, fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
          Tap to expand
        </div>
      )}
    </div>
  );
}

export default function DetailedBreakdownCards({ breakdown }) {
  if (!breakdown) return null;

  return (
    <div style={{ background: 'var(--color-surface)', padding: 'var(--space-6)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-4)' }}>
        <h3 style={{ margin: 0 }}>Detailed Breakdown</h3>
        {breakdown.model_used && (
          <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
            via {breakdown.model_used}
            {breakdown.cached && ' · cached'}
          </span>
        )}
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))',
        gap: 'var(--space-3)',
      }}>
        {COMPONENTS.map(({ key, label, icon }) => (
          <ComponentCard
            key={key}
            icon={icon}
            label={label}
            data={breakdown[key]}
          />
        ))}
      </div>
    </div>
  );
}

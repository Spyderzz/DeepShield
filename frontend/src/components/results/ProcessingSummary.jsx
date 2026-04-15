import { useState } from 'react';

export default function ProcessingSummary({ summary }) {
  const [open, setOpen] = useState(false);
  if (!summary) return null;
  return (
    <div style={{ background: 'var(--color-surface)', borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-sm)' }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          width: '100%',
          textAlign: 'left',
          padding: 'var(--space-4)',
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontWeight: 'var(--font-weight-semibold)',
        }}
      >
        <span>Pipeline summary — {summary.total_duration_ms} ms</span>
        <span>{open ? '▾' : '▸'}</span>
      </button>
      {open && (
        <div style={{ padding: '0 var(--space-4) var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          <div>Model: <b style={{ color: 'var(--color-text-primary)' }}>{summary.model_used}</b></div>
          <ol style={{ margin: 'var(--space-2) 0 0 var(--space-4)' }}>
            {summary.stages_completed.map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

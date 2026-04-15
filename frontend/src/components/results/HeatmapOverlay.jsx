import { useState } from 'react';

export default function HeatmapOverlay({ originalUrl, heatmapBase64 }) {
  const [opacity, setOpacity] = useState(0.6);
  if (!heatmapBase64) {
    return (
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
        No heatmap available.
      </div>
    );
  }
  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
        <figure style={{ margin: 0 }}>
          <figcaption style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>Original</figcaption>
          {originalUrl ? (
            <img src={originalUrl} alt="original" style={{ width: '100%', borderRadius: 'var(--radius-md)' }} />
          ) : (
            <div style={{ color: 'var(--color-text-disabled)' }}>—</div>
          )}
        </figure>
        <figure style={{ margin: 0, position: 'relative' }}>
          <figcaption style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>Heatmap overlay</figcaption>
          <div style={{ position: 'relative', width: '100%' }}>
            {originalUrl && (
              <img src={originalUrl} alt="orig-bg" style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }} />
            )}
            <img
              src={heatmapBase64}
              alt="heatmap"
              style={{
                position: originalUrl ? 'absolute' : 'static',
                top: 0,
                left: 0,
                width: '100%',
                height: originalUrl ? '100%' : 'auto',
                borderRadius: 'var(--radius-md)',
                opacity,
                mixBlendMode: 'multiply',
              }}
            />
          </div>
        </figure>
      </div>
      <div style={{ marginTop: 'var(--space-4)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
        <label htmlFor="hmop" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>Heatmap opacity</label>
        <input
          id="hmop"
          type="range"
          min={0}
          max={1}
          step={0.05}
          value={opacity}
          onChange={(e) => setOpacity(Number(e.target.value))}
          style={{ flex: 1 }}
        />
        <span style={{ fontFamily: 'monospace', fontSize: 'var(--font-size-sm)' }}>{opacity.toFixed(2)}</span>
      </div>
    </div>
  );
}

import { useState } from 'react';

const MODES = [
  { key: 'heatmap', label: 'Heatmap' },
  { key: 'ela', label: 'ELA' },
  { key: 'boxes', label: 'Boxes' },
];

export default function HeatmapOverlay({ originalUrl, heatmapBase64, elaBase64, boxesBase64 }) {
  const [opacity, setOpacity] = useState(0.6);
  const [mode, setMode] = useState('heatmap');

  const overlayMap = {
    heatmap: heatmapBase64,
    ela: elaBase64,
    boxes: boxesBase64,
  };

  const currentOverlay = overlayMap[mode];
  const hasAny = heatmapBase64 || elaBase64 || boxesBase64;

  if (!hasAny) {
    return (
      <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
        No heatmap available.
      </div>
    );
  }

  return (
    <div>
      {/* 3-state toggle */}
      <div style={{ display: 'flex', gap: 'var(--space-1)', marginBottom: 'var(--space-4)', background: 'var(--color-bg, #f4f4f5)', borderRadius: 'var(--radius-md)', padding: '3px', width: 'fit-content' }}>
        {MODES.map((m) => {
          const available = !!overlayMap[m.key];
          return (
            <button
              key={m.key}
              onClick={() => available && setMode(m.key)}
              disabled={!available}
              style={{
                padding: '6px 16px',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: available ? 'pointer' : 'not-allowed',
                fontWeight: mode === m.key ? 'var(--font-weight-semibold)' : 'var(--font-weight-normal)',
                fontSize: 'var(--font-size-sm)',
                background: mode === m.key ? 'var(--color-primary-500)' : 'transparent',
                color: mode === m.key ? 'white' : available ? 'var(--color-text-secondary)' : 'var(--color-text-disabled)',
                transition: 'all 0.2s',
                opacity: available ? 1 : 0.5,
              }}
            >
              {m.label}
            </button>
          );
        })}
      </div>

      {/* Image comparison grid */}
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
          <figcaption style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
            {mode === 'heatmap' && 'Grad-CAM++ overlay'}
            {mode === 'ela' && 'Error Level Analysis'}
            {mode === 'boxes' && 'Suspicious regions'}
          </figcaption>
          <div style={{ position: 'relative', width: '100%' }}>
            {/* For ELA mode, show the ELA map directly (no blend with original) */}
            {mode === 'ela' && currentOverlay ? (
              <img
                src={currentOverlay}
                alt="ela"
                style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }}
              />
            ) : mode === 'boxes' && currentOverlay ? (
              /* Boxes mode: show annotated image directly */
              <img
                src={currentOverlay}
                alt="boxes"
                style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }}
              />
            ) : (
              /* Heatmap mode: overlay with opacity control */
              <>
                {originalUrl && (
                  <img src={originalUrl} alt="orig-bg" style={{ width: '100%', borderRadius: 'var(--radius-md)', display: 'block' }} />
                )}
                {currentOverlay && (
                  <img
                    src={currentOverlay}
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
                )}
              </>
            )}
          </div>
        </figure>
      </div>

      {/* Opacity slider — only for heatmap mode */}
      {mode === 'heatmap' && (
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
      )}

      {/* Mode description */}
      <div style={{ marginTop: 'var(--space-3)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)' }}>
        {mode === 'heatmap' && 'Grad-CAM++ averaged across the last 3 ViT encoder layers. Brighter areas = stronger model activation.'}
        {mode === 'ela' && 'Error Level Analysis: re-saved at JPEG quality 90 and diffed. Brighter regions may indicate manipulation.'}
        {mode === 'boxes' && 'Top suspicious regions extracted from Grad-CAM++ activation. Red = high, orange = medium, yellow = lower suspicion.'}
      </div>
    </div>
  );
}

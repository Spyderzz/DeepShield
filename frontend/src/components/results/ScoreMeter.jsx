import { useEffect, useState } from 'react';
import { scoreColor } from '../../utils/constants.js';

export default function ScoreMeter({ score = 0, size = 200, duration = 1500 }) {
  const [animated, setAnimated] = useState(0);
  useEffect(() => {
    const start = performance.now();
    let raf;
    const step = (t) => {
      const p = Math.min(1, (t - start) / duration);
      setAnimated(p * score);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [score, duration]);

  const r = size / 2 - 14;
  const cx = size / 2;
  const cy = size / 2;
  const sweep = 270; // degrees
  const start = 135; // start angle (bottom-left)

  const polar = (deg) => {
    const rad = (deg - 90) * (Math.PI / 180);
    return [cx + r * Math.cos(rad), cy + r * Math.sin(rad)];
  };
  const [sx, sy] = polar(start);
  const endDeg = start + sweep * (animated / 100);
  const [ex, ey] = polar(endDeg);
  const largeArc = sweep * (animated / 100) > 180 ? 1 : 0;
  const [bex, bey] = polar(start + sweep);

  const color = scoreColor(animated);

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size}>
        <path
          d={`M ${sx} ${sy} A ${r} ${r} 0 1 1 ${bex} ${bey}`}
          fill="none"
          stroke="var(--color-border)"
          strokeWidth={14}
          strokeLinecap="round"
        />
        <path
          d={`M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${ex} ${ey}`}
          fill="none"
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ fontSize: size * 0.22, fontWeight: 'var(--font-weight-bold)', color }}>
          {Math.round(animated)}
        </div>
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          Authenticity
        </div>
      </div>
    </div>
  );
}

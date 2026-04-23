import { useEffect, useState } from 'react';

export default function LayerStack({ src, playing = true, density = 6 }) {
  const [sweep, setSweep] = useState(0);
  useEffect(() => {
    if (!playing) return;
    let raf;
    const start = performance.now();
    const tick = (t) => {
      const dur = 2400;
      const p = ((t - start) % dur) / dur;
      setSweep(p);
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  const layers = Array.from({ length: density });
  const filters = [
    'none',
    'grayscale(1) contrast(1.3)',
    'hue-rotate(180deg) blur(1.5px) saturate(2)',
    'invert(1) hue-rotate(90deg) saturate(1.6) opacity(0.85)',
    'sepia(0.9) hue-rotate(-30deg) saturate(2)',
    'none',
  ];
  const labels = ['SOURCE', 'ARTIFACT', 'HEATMAP', 'ELA', 'FACE MESH', 'COMPOSITE'];

  return (
    <div className="stack-scene">
      <div className="stack-ambient" />
      <div className="stack-deck">
        {layers.map((_, i) => {
          const z = (density - 1 - i) * 36;
          const delay = i * 90;
          return (
            <div key={i} className="stack-layer"
              style={{
                transform: `translateZ(${z}px)`,
                animationDelay: `${delay}ms`,
                filter: filters[i % filters.length],
              }}>
              <div className="stack-layer-inner" style={{ backgroundImage: `url(${src})` }} />
              <span className="stack-tag mono">{labels[i % labels.length]} · L{i+1}</span>
              <div className="stack-laser" style={{ top: `${sweep * 100}%` }} />
            </div>
          );
        })}
        <div className="stack-floor" />
      </div>
      <div className="stack-telemetry">
        <div className="tel-row"><span className="mono">FREQ</span><div className="tel-bar"><i style={{ width: `${30 + sweep*40}%` }}/></div><span className="mono">{(0.72 + sweep*0.2).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">ELA</span><div className="tel-bar"><i style={{ width: `${55 + Math.sin(sweep*Math.PI*2)*15}%`, background: 'var(--ds-warn)' }}/></div><span className="mono">{(0.41 + Math.abs(Math.sin(sweep*Math.PI))*0.3).toFixed(2)}</span></div>
        <div className="tel-row"><span className="mono">FACE</span><div className="tel-bar"><i style={{ width: `${85 - sweep*20}%`, background: 'var(--ds-safe)' }}/></div><span className="mono">{(0.91 - sweep*0.1).toFixed(2)}</span></div>
      </div>
    </div>
  );
}

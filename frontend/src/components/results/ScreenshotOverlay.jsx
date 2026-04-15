import { useEffect, useRef, useState } from 'react';

const SEV_COLOR = { high: '#C62828', medium: '#EF6C00', low: '#2E7D32' };

export default function ScreenshotOverlay({ originalUrl, ocrBoxes = [], suspiciousPhrases = [] }) {
  const imgRef = useRef(null);
  const [dims, setDims] = useState({ natW: 1, natH: 1, showW: 1, showH: 1 });

  const recalc = () => {
    const img = imgRef.current;
    if (!img) return;
    setDims({
      natW: img.naturalWidth || 1,
      natH: img.naturalHeight || 1,
      showW: img.clientWidth || 1,
      showH: img.clientHeight || 1,
    });
  };

  useEffect(() => {
    window.addEventListener('resize', recalc);
    return () => window.removeEventListener('resize', recalc);
  }, []);

  if (!originalUrl) return null;
  const sx = dims.showW / dims.natW;
  const sy = dims.showH / dims.natH;

  const phraseBoxKeys = new Set(suspiciousPhrases.map((p) => JSON.stringify(p.bbox)));

  const renderBox = (bbox, color, fill, strokeW = 2) => {
    const xs = bbox.map((p) => p[0]);
    const ys = bbox.map((p) => p[1]);
    const left = Math.min(...xs) * sx;
    const top = Math.min(...ys) * sy;
    const w = (Math.max(...xs) - Math.min(...xs)) * sx;
    const h = (Math.max(...ys) - Math.min(...ys)) * sy;
    return (
      <div
        style={{
          position: 'absolute', left, top, width: w, height: h,
          border: `${strokeW}px solid ${color}`, background: fill, pointerEvents: 'none',
        }}
      />
    );
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block', maxWidth: '100%' }}>
      <img
        ref={imgRef}
        src={originalUrl}
        alt="screenshot"
        onLoad={recalc}
        style={{ maxWidth: '100%', height: 'auto', display: 'block', borderRadius: 'var(--radius-md)' }}
      />
      {ocrBoxes.map((b, i) => {
        const key = JSON.stringify(b.bbox);
        if (phraseBoxKeys.has(key)) return null;
        return <div key={`o${i}`}>{renderBox(b.bbox, 'rgba(33,150,243,0.5)', 'rgba(33,150,243,0.08)', 1)}</div>;
      })}
      {suspiciousPhrases.map((p, i) => {
        const c = SEV_COLOR[p.severity] || '#EF6C00';
        return (
          <div key={`s${i}`} title={`${p.text} · ${p.description}`}>
            {renderBox(p.bbox, c, `${c}22`, 3)}
          </div>
        );
      })}
    </div>
  );
}

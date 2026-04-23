import { useRef, useState, useEffect } from 'react';

export default function ScrollReveal({ 
  children, 
  maxBlur = 18, 
  startOffset = 0.8, 
  endOffset = 0.4 
}) {
  const ref = useRef(null);
  const [reveal, setReveal] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      if (!ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const h = window.innerHeight;
      
      const start = h * startOffset;
      const end = h * endOffset;
      const raw = (start - rect.top) / (start - end);
      
      // Clamp the value between 0 (fully blurred) and 1 (fully revealed)
      setReveal(Math.max(0, Math.min(1, raw)));
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll(); // Trigger once on mount
    return () => window.removeEventListener('scroll', onScroll);
  }, [startOffset, endOffset]);

  const blur = (1 - reveal) * maxBlur;
  const opacity = 0.2 + (reveal * 0.8);

  return (
    <span 
      ref={ref} 
      style={{ 
        filter: `blur(${blur}px)`, 
        opacity: opacity,
        display: 'inline-block',
        willChange: 'filter, opacity'
      }}
    >
      {children}
    </span>
  );
}

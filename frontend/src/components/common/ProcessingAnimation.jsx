import { motion } from 'framer-motion';

const LAYER_FILTERS = [
  'none',
  'grayscale(1) contrast(1.4)',
  'hue-rotate(60deg) saturate(2.2)',
  'sepia(0.7) contrast(1.3)',
  'invert(0.15) hue-rotate(200deg)',
  'hue-rotate(280deg) blur(1.5px) saturate(2)',
];

const LAYER_OPACITIES = [1, 0.80, 0.64, 0.50, 0.38, 0.26];
const Z_GAP = 40;
const W = 360;
const H = 240;

function ScannerBar() {
  return (
    <motion.div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        height: 2,
        background: 'linear-gradient(90deg, transparent, rgba(30,136,229,0.9) 30%, rgba(0,229,255,0.9) 70%, transparent)',
        boxShadow: '0 0 10px rgba(0,229,255,0.6), 0 0 20px rgba(30,136,229,0.3)',
        pointerEvents: 'none',
        zIndex: 10,
      }}
      initial={{ top: '0%', opacity: 0 }}
      animate={{ top: ['0%', '100%', '0%'], opacity: [0, 1, 1, 0.8, 0] }}
      transition={{ duration: 2.4, repeat: Infinity, ease: 'easeInOut', delay: 0.8 }}
    />
  );
}

export default function ProcessingAnimation({ imageUrl, mediaType = 'image', label = 'Analyzing…' }) {
  const showImageLayers = !!imageUrl && (mediaType === 'image' || mediaType === 'screenshot');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-6)', padding: 'var(--space-8) 0' }}>
      <div style={{ perspective: 1100, perspectiveOrigin: '50% 40%', width: W, height: H + 80 }}>
        <motion.div
          style={{
            transformStyle: 'preserve-3d',
            position: 'relative',
            width: W,
            height: H,
            marginTop: 40,
          }}
          initial={{ rotateX: 52, rotateZ: -28, scale: 0.85, opacity: 0 }}
          animate={{ rotateX: 52, rotateZ: -28, scale: 1, opacity: 1 }}
          transition={{ duration: 0.7, ease: [0.34, 1.56, 0.64, 1] }}
        >
          {LAYER_FILTERS.map((filter, i) => (
            <motion.div
              key={i}
              style={{
                position: 'absolute',
                inset: 0,
                borderRadius: 10,
                overflow: 'hidden',
                willChange: 'transform',
              }}
              initial={{ z: 0, opacity: 0 }}
              animate={{ z: i * Z_GAP, opacity: showImageLayers ? LAYER_OPACITIES[i] : LAYER_OPACITIES[i] * 0.75 }}
              transition={{ delay: i * 0.08, type: 'spring', stiffness: 280, damping: 28 }}
            >
              {showImageLayers ? (
                <>
                  <img
                    src={imageUrl}
                    alt=""
                    style={{ width: '100%', height: '100%', objectFit: 'cover', filter, display: 'block' }}
                  />
                  {i === 0 && <ScannerBar />}
                </>
              ) : (
                <div
                  style={{
                    width: '100%',
                    height: '100%',
                    background: `linear-gradient(135deg, hsla(${210 + i * 25}, 70%, 60%, 0.20), hsla(${240 + i * 20}, 70%, 50%, 0.14))`,
                    border: `1px solid hsla(${210 + i * 25}, 70%, 70%, 0.24)`,
                    position: 'relative',
                  }}
                >
                  {i === 0 && <ScannerBar />}
                </div>
              )}
            </motion.div>
          ))}
        </motion.div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <motion.p
          style={{
            margin: 0,
            fontSize: 'var(--font-size-sm)',
            color: 'var(--color-text-secondary)',
            fontWeight: 'var(--font-weight-medium)',
            letterSpacing: '0.03em',
          }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
        >
          {label}
        </motion.p>
        <div style={{ display: 'flex', gap: 6, justifyContent: 'center', marginTop: 'var(--space-2)' }}>
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary-400)' }}
              animate={{ scale: [1, 1.5, 1], opacity: [0.35, 1, 0.35] }}
              transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.22, ease: 'easeInOut' }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

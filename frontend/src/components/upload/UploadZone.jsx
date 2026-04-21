import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';

const ACCEPT = {
  image: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
  video: { 'video/mp4': [], 'video/webm': [], 'video/quicktime': [], 'video/x-msvideo': [] },
  screenshot: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
};

const HINT = {
  image: 'JPEG · PNG · WebP',
  video: 'MP4 · WebM · MOV · AVI',
  screenshot: 'JPEG · PNG · WebP (news / social screenshot)',
};

function UploadIcon({ active, color }) {
  return (
    <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      {active ? (
        <>
          <path d="M12 19V5" />
          <path d="M5 12l7-7 7 7" />
        </>
      ) : (
        <>
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </>
      )}
    </svg>
  );
}

export default function UploadZone({ mediaType = 'image', maxSizeMB = 20, onFileAccepted, disabled = false }) {
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);

  const onDrop = useCallback(
    (accepted, rejections) => {
      setError(null);
      if (rejections?.length) {
        setError(rejections[0].errors?.[0]?.message || 'File rejected');
        return;
      }
      const file = accepted[0];
      if (!file) return;
      if (file.size > maxSizeMB * 1024 * 1024) {
        setError(`File too large — max ${maxSizeMB} MB`);
        return;
      }
      setPreview(URL.createObjectURL(file));
      onFileAccepted?.(file);
    },
    [maxSizeMB, onFileAccepted],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT[mediaType],
    multiple: false,
    disabled,
    maxFiles: 1,
  });

  const iconColor = isDragActive ? '#1E88E5' : disabled ? '#BDBDBD' : '#9E9E9E';

  return (
    <div>
      <motion.div
        {...getRootProps()}
        whileHover={!disabled ? { y: -2 } : {}}
        style={{
          border: `2px dashed ${isDragActive ? '#1E88E5' : '#E0E0E0'}`,
          borderRadius: 'var(--radius-xl)',
          minHeight: 300,
          padding: 'var(--space-12) var(--space-8)',
          background: isDragActive ? 'rgba(30,136,229,0.05)' : 'transparent',
          boxShadow: isDragActive ? '0 0 0 3px rgba(30,136,229,0.12), inset 0 0 40px rgba(30,136,229,0.04)' : 'none',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'all 0.2s ease',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 'var(--space-3)',
        }}
      >
        <input {...getInputProps()} />

        <motion.div
          animate={isDragActive ? { scale: 1.18, y: -4 } : { scale: 1, y: 0 }}
          transition={{ type: 'spring', stiffness: 320, damping: 22 }}
        >
          <UploadIcon active={isDragActive} color={iconColor} />
        </motion.div>

        <div style={{
          fontSize: 'var(--font-size-lg)',
          color: isDragActive ? 'var(--color-primary-600)' : 'var(--color-text-primary)',
          fontWeight: 'var(--font-weight-semibold)',
          transition: 'color 0.2s',
        }}>
          {isDragActive ? `Drop to analyze…` : `Drop your ${mediaType} here`}
        </div>

        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          or{' '}
          <span style={{ color: 'var(--color-primary-500)', fontWeight: 'var(--font-weight-medium)' }}>
            click to browse
          </span>
        </div>

        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-disabled)', marginTop: 'var(--space-1)' }}>
          {HINT[mediaType]} · up to {maxSizeMB} MB
        </div>
      </motion.div>

      {preview && (mediaType === 'image' || mediaType === 'screenshot') && (
        <div style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
          <img
            src={preview}
            alt="preview"
            style={{ maxHeight: 220, borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }}
          />
        </div>
      )}
      {preview && mediaType === 'video' && (
        <div style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
          <video
            src={preview}
            controls
            style={{ maxHeight: 220, borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }}
          />
        </div>
      )}
      {error && (
        <div style={{ marginTop: 'var(--space-3)', color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)' }}>
          {error}
        </div>
      )}
    </div>
  );
}

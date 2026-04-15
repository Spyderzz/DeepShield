import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';

const ACCEPT = {
  image: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
  video: { 'video/mp4': [], 'video/webm': [], 'video/quicktime': [], 'video/x-msvideo': [] },
  screenshot: { 'image/jpeg': [], 'image/png': [], 'image/webp': [] },
};

const HINT = {
  image: 'JPEG · PNG · WebP',
  video: 'MP4 · WebM · MOV · AVI',
  screenshot: 'JPEG · PNG · WebP (news/social screenshot)',
};

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
    [maxSizeMB, onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT[mediaType],
    multiple: false,
    disabled,
    maxFiles: 1,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        style={{
          border: `2px dashed ${isDragActive ? 'var(--color-primary-500)' : 'var(--color-border)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: 'var(--space-10)',
          background: isDragActive ? 'var(--color-primary-50)' : 'var(--color-surface)',
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          transition: 'all var(--transition-base)',
        }}
      >
        <input {...getInputProps()} />
        <div style={{ fontSize: 'var(--font-size-lg)', color: 'var(--color-text-primary)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-2)' }}>
          {isDragActive ? `Drop the ${mediaType} here…` : `Drag & drop a ${mediaType}, or click to browse`}
        </div>
        <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
          {HINT[mediaType]} · up to {maxSizeMB} MB
        </div>
      </div>

      {preview && (mediaType === 'image' || mediaType === 'screenshot') && (
        <div style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
          <img
            src={preview}
            alt="preview"
            style={{ maxHeight: 240, borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }}
          />
        </div>
      )}
      {preview && mediaType === 'video' && (
        <div style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
          <video
            src={preview}
            controls
            style={{ maxHeight: 240, borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-md)' }}
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

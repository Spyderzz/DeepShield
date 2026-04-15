export default function Skeleton({ width = '100%', height = 16, radius = 'var(--radius-sm)', style = {} }) {
  return (
    <div
      className="skeleton-pulse"
      style={{
        width,
        height,
        background: 'linear-gradient(90deg, #EEEEEE 0%, #F5F5F5 50%, #EEEEEE 100%)',
        backgroundSize: '200% 100%',
        borderRadius: radius,
        ...style,
      }}
    />
  );
}

export function SkeletonCard({ lines = 3 }) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-md)',
      padding: 'var(--space-4)',
      display: 'grid',
      gap: 'var(--space-2)',
    }}>
      <Skeleton height={24} width="40%" />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} height={14} width={`${70 + ((i * 13) % 30)}%`} />
      ))}
    </div>
  );
}

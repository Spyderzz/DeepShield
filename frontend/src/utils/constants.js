export const SEVERITY_COLORS = {
  critical: 'var(--color-danger)',
  danger: '#E57373',
  warning: 'var(--color-warning)',
  positive: '#81C784',
  safe: 'var(--color-safe)',
};

export function scoreColor(score) {
  const lerp = (a, b, t) => Math.round(a + (b - a) * t);
  const s = Math.max(0, Math.min(100, score));
  if (s <= 50) {
    const t = s / 50;
    return `rgb(${lerp(0xe5, 0xff, t)}, ${lerp(0x39, 0xa7, t)}, ${lerp(0x35, 0x26, t)})`;
  }
  const t = (s - 50) / 50;
  return `rgb(${lerp(0xff, 0x43, t)}, ${lerp(0xa7, 0xa0, t)}, ${lerp(0x26, 0x47, t)})`;
}

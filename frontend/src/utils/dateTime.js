const IST_TIME_ZONE = 'Asia/Kolkata';

const DATE_TIME_IST_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: IST_TIME_ZONE,
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hour12: true,
});

const DATE_IST_FORMATTER = new Intl.DateTimeFormat('en-IN', {
  timeZone: IST_TIME_ZONE,
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

function toValidDate(value) {
  if (!value) return null;
  const d = value instanceof Date ? value : new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

export function formatDateTimeIST(value, fallback = '—') {
  const d = toValidDate(value);
  return d ? DATE_TIME_IST_FORMATTER.format(d) : fallback;
}

export function formatDateIST(value, fallback = '—') {
  const d = toValidDate(value);
  return d ? DATE_IST_FORMATTER.format(d) : fallback;
}

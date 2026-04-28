import { api } from './api.js';

export async function generateReport(recordId, token = null) {
  const url = token ? `/report/${recordId}?token=${token}` : `/report/${recordId}`;
  const { data } = await api.post(url, null, { timeout: 60000 });
  return data;
}

export function reportDownloadUrl(recordId) {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
  return `${base}/report/${recordId}/download`;
}

export async function downloadReportBlob(recordId, token = null) {
  const url = token ? `/report/${recordId}/download?token=${token}` : `/report/${recordId}/download`;
  const { data } = await api.get(url, { responseType: 'blob', timeout: 30000 });
  return data;
}

export function saveReportBlob(blob, recordId) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `deepshield_report_${recordId}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

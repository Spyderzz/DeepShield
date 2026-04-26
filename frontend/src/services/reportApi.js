import { api } from './api.js';

export async function generateReport(recordId) {
  const { data } = await api.post(`/report/${recordId}`, null, { timeout: 60000 });
  return data;
}

export function reportDownloadUrl(recordId) {
  const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');
  return `${base}/report/${recordId}/download`;
}

export async function downloadReportBlob(recordId) {
  const { data } = await api.get(`/report/${recordId}/download`, { responseType: 'blob', timeout: 30000 });
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

import { api } from './api.js';

export async function generateReport(recordId) {
  const { data } = await api.post(`/report/${recordId}`, null, { timeout: 60000 });
  return data;
}

export function reportDownloadUrl(recordId) {
  // axios baseURL is /api/v1; return absolute path for <a download>
  return `/api/v1/report/${recordId}/download`;
}

export async function downloadReportBlob(recordId) {
  const { data } = await api.get(`/report/${recordId}/download`, { responseType: 'blob', timeout: 30000 });
  return data;
}

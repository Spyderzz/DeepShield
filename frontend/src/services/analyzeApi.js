import { api } from './api.js';

export async function analyzeImage(file) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/image', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function analyzeVideo(file) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/video', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return data;
}

export async function analyzeText(text) {
  const { data } = await api.post('/analyze/text', { text });
  return data;
}

export async function analyzeScreenshot(file) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/screenshot', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 180000,
  });
  return data;
}

// Phase 19.3 — async video with job polling
export async function submitVideoJob(file) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/video/async', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  });
  return data; // { job_id, status, cached }
}

export async function getJob(jobId) {
  const { data } = await api.get(`/jobs/${jobId}`);
  return data; // { id, status, stage, progress, error, result }
}

export async function pollVideoJob(jobId, { onProgress, intervalMs = 800, timeoutMs = 300000 } = {}) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const job = await getJob(jobId);
    if (onProgress) onProgress(job);
    if (job.status === 'done') return job.result;
    if (job.status === 'error') throw new Error(job.error || 'Job failed');
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  throw new Error('Video job timed out');
}

// Phase 19.5 — readiness probe
export async function getReadiness() {
  try {
    const { data, status } = await api.get('/health/ready', { validateStatus: () => true });
    return { ready: status === 200, ...data };
  } catch (_e) {
    return { ready: false, checks: {} };
  }
}

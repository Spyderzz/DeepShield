import { api } from './api.js';

function cleanOptions(options = {}) {
  return {
    cache: options.cache !== false,
    language_hint: options.languageHint || 'auto',
  };
}

export async function analyzeImage(file, options) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/image', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: cleanOptions(options),
  });
  return data;
}

export async function analyzeVideo(file, options) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/video', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: cleanOptions(options),
    timeout: 300000,
  });
  return data;
}

export async function analyzeText(text, options) {
  const { data } = await api.post('/analyze/text', {
    text,
    cache: options?.cache !== false,
    language_hint: options?.languageHint || 'auto',
  });
  return data;
}

export async function analyzeScreenshot(file, options = {}) {
  const { cache = true, languageHint = 'auto' } = options;
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post(`/analyze/screenshot?cache=${cache}&language_hint=${languageHint}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function analyzeAudio(file, options = {}) {
  const { cache = true, languageHint = 'en' } = options;
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post(`/analyze/audio?cache=${cache}&language_hint=${languageHint}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  });
  return res.data;
}

// Phase 19.3 — async video with job polling
export async function submitVideoJob(file, options) {
  const fd = new FormData();
  fd.append('file', file);
  const { data } = await api.post('/analyze/video/async', fd, {
    headers: { 'Content-Type': 'multipart/form-data' },
    params: cleanOptions(options),
    timeout: 300000,
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

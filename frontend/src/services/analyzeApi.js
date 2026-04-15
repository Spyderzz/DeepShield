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

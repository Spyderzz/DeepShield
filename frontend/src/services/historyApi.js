import { api } from './api.js';

export async function listHistory(limit = 50, offset = 0) {
  const { data } = await api.get('/history', { params: { limit, offset } });
  return data;
}

export async function getHistoryDetail(id, token = null) {
  const { data } = await api.get(`/history/${id}`, {
    params: token ? { token } : undefined,
  });
  return data;
}

export async function deleteHistory(id) {
  await api.delete(`/history/${id}`);
}

export async function clearHistory() {
  const { data } = await api.delete('/history');
  return data;
}

import { api } from './api.js';

export async function listHistory(limit = 50, offset = 0) {
  const { data } = await api.get('/history', { params: { limit, offset } });
  return data;
}

export async function getHistoryDetail(id) {
  const { data } = await api.get(`/history/${id}`);
  return data;
}

export async function deleteHistory(id) {
  await api.delete(`/history/${id}`);
}

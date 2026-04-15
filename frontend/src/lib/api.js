const BASE = '/api';

export class ApiError extends Error {
  constructor(status, detail) {
    super(detail?.detail ?? `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export const getToken = () => localStorage.getItem('keg_token');
export const setToken = (t) => localStorage.setItem('keg_token', t);
export const clearToken = () => localStorage.removeItem('keg_token');
export const isLoggedIn = () => !!getToken();

async function request(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) throw new ApiError(res.status, await res.json());
  return res.json();
}

export const fetchKegs = () => request('/kegs');
export const fetchKeg = (id) => request(`/kegs/${id}`);
export const updateKeg = (id, data) => request(`/kegs/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const patchKegStatus = (id, status) => request(`/kegs/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
export const clearKeg = (id) => request(`/kegs/${id}`, { method: 'DELETE' });
export const login = (username, password) =>
  request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });

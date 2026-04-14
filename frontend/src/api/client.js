const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getLOBMetrics: (hours = 24) => request(`/metrics/lob?hours=${hours}`),
  getChartData: (hours = 24) => request(`/metrics/chart-data?hours=${hours}`),
  getBottlenecks: (hours = 24) => request(`/bottlenecks?hours=${hours}`),
  getPharmacyMetrics: (hours = 24) => request(`/pharmacy/metrics?hours=${hours}`),
  getAlerts: () => request('/alerts'),
  getSummary: (hours = 24) => request(`/data/summary?hours=${hours}`),
  refreshData: () => request('/data/refresh', { method: 'POST' }),
  runSimulation: (params) => request('/simulation/compare', { method: 'POST', body: JSON.stringify(params) }),
  chat: (message) => request('/chat', { method: 'POST', body: JSON.stringify({ message }) }),
};

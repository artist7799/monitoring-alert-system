import api from './axios';

export const statusApi = {
  getOverview: async () => {
    const response = await api.get('/api/status/overview');
    return response.data;
  },

  getDeviceStatusList: async (params = {}) => {
    const response = await api.get('/api/status/devices', { params });
    return response.data;
  },

  getDeviceStatusById: async (id) => {
    const response = await api.get(`/api/status/devices/${id}`);
    return response.data;
  },

  getRecentEvents: async (limit = 10) => {
    const response = await api.get('/api/status/recent-events', { params: { limit } });
    return response.data;
  },

  getRecentAlerts: async (limit = 10) => {
    const response = await api.get('/api/status/recent-alerts', { params: { limit } });
    return response.data;
  }
};

import api from './axios';

export const alertApi = {
  getAlerts: async (params = {}) => {
    const response = await api.get('/api/alerts', { params });
    return response.data;
  },

  getAlertById: async (id) => {
    const response = await api.get(`/api/alerts/${id}`);
    return response.data;
  },

  acknowledgeAlert: async (id, data = {}) => {
    const response = await api.post(`/api/alerts/${id}/acknowledge`, data);
    return response.data;
  },

  resolveAlert: async (id, data = {}) => {
    const response = await api.post(`/api/alerts/${id}/resolve`, data);
    return response.data;
  }
};

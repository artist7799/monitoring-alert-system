import api from './axios';

export const deviceApi = {
  getDevices: async (params = {}) => {
    const response = await api.get('/api/devices', { params });
    return response.data;
  },

  getDeviceById: async (id) => {
    const response = await api.get(`/api/devices/${id}`);
    return response.data;
  },

  createDevice: async (deviceData) => {
    const response = await api.post('/api/devices', deviceData);
    return response.data;
  },

  updateDevice: async (id, deviceData) => {
    const response = await api.put(`/api/devices/${id}`, deviceData);
    return response.data;
  },

  deleteDevice: async (id) => {
    const response = await api.delete(`/api/devices/${id}`);
    return response.data;
  }
};

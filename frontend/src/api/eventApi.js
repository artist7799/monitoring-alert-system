import api from './axios';

export const eventApi = {
  getEvents: async (params = {}) => {
    const response = await api.get('/api/events', { params });
    return response.data;
  },

  getEventById: async (id) => {
    const response = await api.get(`/api/events/${id}`);
    return response.data;
  },

  createEvent: async (eventData) => {
    const response = await api.post('/api/events', eventData);
    return response.data;
  }
};

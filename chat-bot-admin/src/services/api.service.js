// src/services/api.service.js
// API service for connecting to the backend

import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

console.log('Using API URL:', API_URL);

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add interceptor to include auth token in requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor to handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 (Unauthorized) and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh token (implement refreshToken method)
        // const refreshToken = localStorage.getItem('refreshToken');
        // const response = await refreshTokenCall(refreshToken);
        // const newToken = response.data.token;
        // localStorage.setItem('token', newToken);
        
        // originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        // return api(originalRequest);
        
        // For now just log out the user
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      } catch (refreshError) {
        // If refresh fails, log out user
        localStorage.removeItem('token');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API calls
const AuthService = {
  register: async (email, password) => {
    const response = await api.post('/auth/register', { email, password });
    return response.data;
  },
  
  login: async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('refreshToken', response.data.refreshToken);
      localStorage.setItem('user', JSON.stringify({
        id: response.data.userId,
        email: response.data.email
      }));
    }
    return response.data;
  },
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  updatePreferences: async (preferences) => {
    const response = await api.patch('/auth/preferences', preferences);
    return response.data;
  },
  
  getUser: () => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr);
    }
    return null;
  },
  
  isLoggedIn: () => {
    return !!localStorage.getItem('token');
  }
};

// Creators API calls
const CreatorService = {
  getAll: async () => {
    const response = await api.get('/creators');
    return response.data;
  },
  
  getById: async (id) => {
    const response = await api.get(`/creators/${id}`);
    return response.data;
  },
  
  create: async (creatorData) => {
    const response = await api.post('/creators', creatorData);
    return response.data;
  },
  
  update: async (id, creatorData) => {
    const response = await api.patch(`/creators/${id}`, creatorData);
    return response.data;
  },
  
  updateStyle: async (id, styleData) => {
    const response = await api.patch(`/creators/${id}/style`, styleData);
    return response.data;
  },
  
  addExample: async (id, exampleData) => {
    const response = await api.post(`/creators/${id}/examples`, exampleData);
    return response.data;
  }
};

// Export all services
export { api, AuthService, CreatorService };
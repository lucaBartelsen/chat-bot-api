// src/contexts/AuthContext.jsx
// Authentication context provider for managing user auth state

import React, { createContext, useContext, useState, useEffect } from 'react';
import { AuthService } from '../services/api.service';

// Create the authentication context
const AuthContext = createContext(null);

// Create provider component
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is logged in on mount
    const checkLoggedIn = async () => {
      if (AuthService.isLoggedIn()) {
        try {
          // Get current user data from API
          const response = await AuthService.getCurrentUser();
          setUser(response.user);
        } catch (err) {
          console.error('Error fetching user:', err);
          setError('Session expired. Please log in again.');
          AuthService.logout();
        }
      }
      setLoading(false);
    };

    checkLoggedIn();
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      setError(null);
      const response = await AuthService.login(email, password);
      setUser({
        id: response.userId,
        email: response.email,
        preferences: response.preferences
      });
      return response;
    } catch (err) {
      const message = err.response?.data?.message || 'Login failed';
      setError(message);
      throw new Error(message);
    }
  };

  // Register function
  const register = async (email, password) => {
    try {
      setError(null);
      const response = await AuthService.register(email, password);
      return response;
    } catch (err) {
      const message = err.response?.data?.message || 'Registration failed';
      setError(message);
      throw new Error(message);
    }
  };

  // Logout function
  const logout = () => {
    AuthService.logout();
    setUser(null);
  };

  // Update user preferences
  const updatePreferences = async (preferences) => {
    try {
      const response = await AuthService.updatePreferences(preferences);
      setUser(prev => ({
        ...prev,
        preferences: response.preferences
      }));
      return response;
    } catch (err) {
      const message = err.response?.data?.message || 'Failed to update preferences';
      setError(message);
      throw new Error(message);
    }
  };

  // Context value
  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    updatePreferences,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

// Custom hook for using the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export default AuthContext;
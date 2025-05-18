// src/App.jsx
// Main application component with routing configuration

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { AuthProvider, useAuth } from './contexts/AuthContext';

// Auth Components
import Login from './components/auth/Login';
import Register from './components/auth/Register';

// Creator Components
import Dashboard from './components/dashboard/Dashboard';
import CreatorForm from './components/creators/CreatorForm';
import CreatorDetail from './components/creators/CreatorDetail';
import StyleEditor from './components/creators/StyleEditor';
import ExamplesManager from './components/creators/ExamplesManager';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex justify-center items-center bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

function App() {
  return (
    <Router>
      <AuthProvider>
        <ToastContainer position="top-right" autoClose={3000} />
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Navigate to="/dashboard" replace />
            </ProtectedRoute>
          } />
          
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />

          <Route path="/creators/new" element={
            <ProtectedRoute>
              <CreatorForm />
            </ProtectedRoute>
          } />

          <Route path="/creators/:id" element={
            <ProtectedRoute>
              <CreatorDetail />
            </ProtectedRoute>
          } />

          <Route path="/creators/:id/edit" element={
            <ProtectedRoute>
              <CreatorForm />
            </ProtectedRoute>
          } />

          <Route path="/creators/:id/style" element={
            <ProtectedRoute>
              <StyleEditor />
            </ProtectedRoute>
          } />

          <Route path="/creators/:id/examples" element={
            <ProtectedRoute>
              <ExamplesManager />
            </ProtectedRoute>
          } />

          {/* 404 Route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
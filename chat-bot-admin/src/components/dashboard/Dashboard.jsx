// src/components/dashboard/Dashboard.jsx
// Main dashboard component showing creator profiles list

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { CreatorService } from '../../services/api.service';
import { useAuth } from '../../contexts/AuthContext';
import { FiPlus, FiEdit2, FiUser } from 'react-icons/fi';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const [creators, setCreators] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load creators on component mount
    const fetchCreators = async () => {
      try {
        setLoading(true);
        const response = await CreatorService.getAll();
        setCreators(response.creators || []);
      } catch (error) {
        console.error('Error fetching creators:', error);
        toast.error('Failed to load creators');
      } finally {
        setLoading(false);
      }
    };

    fetchCreators();
  }, []);

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="bg-purple-600 pb-32">
        <nav className="bg-purple-600 border-b border-purple-300 border-opacity-25 lg:border-none">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-white text-xl font-bold">FanFix ChatAssist</h1>
                </div>
              </div>
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <button
                    className="relative inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-800 shadow-sm hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                    onClick={logout}
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>
        <header className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-white">
              Creator Profiles Dashboard
            </h1>
            <p className="mt-2 text-white">
              Manage creator profiles and writing styles
            </p>
          </div>
        </header>
      </div>

      {/* Main content */}
      <main className="-mt-32">
        <div className="max-w-7xl mx-auto pb-12 px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow px-5 py-6 sm:px-6">
            {/* User info card */}
            <div className="bg-purple-50 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <FiUser className="h-8 w-8 text-purple-600 mr-4" />
                <div>
                  <h2 className="text-lg font-medium text-gray-900">
                    Welcome, {user?.email}
                  </h2>
                  <p className="text-sm text-gray-600">
                    Admin access: Create and manage creator profiles
                  </p>
                </div>
              </div>
            </div>

            {/* Creators header with add button */}
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg leading-6 font-medium text-gray-900">Creator Profiles</h2>
              <Link
                to="/creators/new"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
              >
                <FiPlus className="mr-2" />
                Add Creator
              </Link>
            </div>

            {/* Creators list */}
            {loading ? (
              <div className="py-12 text-center">
                <div className="spinner"></div>
                <p className="mt-4 text-gray-500">Loading creators...</p>
              </div>
            ) : creators.length === 0 ? (
              <div className="text-center py-12 bg-gray-50 rounded-lg">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                  />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900">No creators</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating a new creator profile.
                </p>
                <div className="mt-6">
                  <Link
                    to="/creators/new"
                    className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                  >
                    <FiPlus className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
                    Add Creator
                  </Link>
                </div>
              </div>
            ) : (
              <div className="bg-white shadow overflow-hidden sm:rounded-md">
                <ul className="divide-y divide-gray-200">
                  {creators.map((creator) => (
                    <li key={creator.id}>
                      <div className="block hover:bg-gray-50">
                        <div className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              {creator.avatar_url ? (
                                <img
                                  className="h-10 w-10 rounded-full"
                                  src={creator.avatar_url}
                                  alt={creator.name}
                                />
                              ) : (
                                <div className="h-10 w-10 rounded-full bg-purple-200 flex items-center justify-center">
                                  <span className="text-purple-600 font-medium text-sm">
                                    {creator.name?.charAt(0).toUpperCase() || '?'}
                                  </span>
                                </div>
                              )}
                              <div className="ml-4">
                                <p className="text-sm font-medium text-purple-600 truncate">{creator.name}</p>
                                <p className="text-sm text-gray-500 truncate">
                                  {creator.description || 'No description'}
                                </p>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Link
                                to={`/creators/${creator.id}`}
                                className="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-purple-700 bg-purple-100 hover:bg-purple-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                              >
                                View
                              </Link>
                              <Link
                                to={`/creators/${creator.id}/edit`}
                                className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                              >
                                <FiEdit2 className="mr-1" />
                                Edit
                              </Link>
                            </div>
                          </div>
                          <div className="mt-2 sm:flex sm:justify-between">
                            <div className="sm:flex">
                              <p className="flex items-center text-sm text-gray-500">
                                Status: 
                                <span className={`ml-1 px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${creator.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                                  {creator.active ? 'Active' : 'Inactive'}
                                </span>
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
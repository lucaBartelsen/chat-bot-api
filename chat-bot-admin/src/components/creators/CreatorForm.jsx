// src/components/creators/CreatorForm.jsx
// Form component for adding and editing creator profiles

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Formik, Form, Field, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { toast } from 'react-toastify';
import { CreatorService } from '../../services/api.service';
import { FiSave, FiArrowLeft } from 'react-icons/fi';

const CreatorForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEditMode = !!id;
  const [creator, setCreator] = useState(null);
  const [loading, setLoading] = useState(isEditMode);

  useEffect(() => {
    // If in edit mode, fetch creator data
    if (isEditMode) {
      const fetchCreator = async () => {
        try {
          setLoading(true);
          const response = await CreatorService.getById(id);
          setCreator(response.creator);
        } catch (error) {
          console.error('Error fetching creator:', error);
          toast.error('Failed to load creator data');
          navigate('/dashboard');
        } finally {
          setLoading(false);
        }
      };

      fetchCreator();
    }
  }, [id, isEditMode, navigate]);

  // Validation schema
  const validationSchema = Yup.object({
    name: Yup.string().required('Name is required'),
    description: Yup.string(),
    avatar_url: Yup.string().url('Must be a valid URL').nullable(),
    active: Yup.boolean()
  });

  // Initial form values
  const initialValues = {
    name: creator?.name || '',
    description: creator?.description || '',
    avatar_url: creator?.avatar_url || '',
    active: creator?.active !== undefined ? creator.active : true
  };

  // Handle form submission
  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      if (isEditMode) {
        await CreatorService.update(id, values);
        toast.success('Creator updated successfully');
      } else {
        const response = await CreatorService.create(values);
        toast.success('Creator created successfully');
        navigate(`/creators/${response.creator.id}`);
      }
    } catch (error) {
      console.error('Error saving creator:', error);
      toast.error(error.response?.data?.message || 'Failed to save creator');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex justify-center items-center">
        <div className="spinner"></div>
        <p className="ml-2">Loading creator data...</p>
      </div>
    );
  }

  return (
    <div className="min-h-full">
      {/* Header */}
      <div className="bg-purple-600 pb-32">
        <nav className="bg-purple-600 border-b border-purple-300 border-opacity-25 lg:border-none">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex items-center">
                <Link to="/dashboard" className="flex-shrink-0 text-white flex items-center">
                  <FiArrowLeft className="mr-2" />
                  Back to Dashboard
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <header className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-white">
              {isEditMode ? 'Edit Creator Profile' : 'Create New Creator Profile'}
            </h1>
          </div>
        </header>
      </div>

      {/* Main content */}
      <main className="-mt-32">
        <div className="max-w-7xl mx-auto pb-12 px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow px-5 py-6 sm:px-6">
            <Formik
              initialValues={initialValues}
              validationSchema={validationSchema}
              onSubmit={handleSubmit}
              enableReinitialize
            >
              {({ isSubmitting, values }) => (
                <Form className="space-y-6">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Name *
                    </label>
                    <div className="mt-1">
                      <Field
                        id="name"
                        name="name"
                        type="text"
                        className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      />
                      <ErrorMessage name="name" component="div" className="mt-1 text-sm text-red-600" />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                      Description
                    </label>
                    <div className="mt-1">
                      <Field
                        as="textarea"
                        id="description"
                        name="description"
                        rows={3}
                        className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      />
                      <ErrorMessage name="description" component="div" className="mt-1 text-sm text-red-600" />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Brief description of the creator
                    </p>
                  </div>

                  <div>
                    <label htmlFor="avatar_url" className="block text-sm font-medium text-gray-700">
                      Avatar URL
                    </label>
                    <div className="mt-1">
                      <Field
                        id="avatar_url"
                        name="avatar_url"
                        type="text"
                        className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      />
                      <ErrorMessage name="avatar_url" component="div" className="mt-1 text-sm text-red-600" />
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      URL to the creator's avatar image
                    </p>
                  </div>

                  <div className="flex items-center">
                    <Field
                      id="active"
                      name="active"
                      type="checkbox"
                      className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                    />
                    <label htmlFor="active" className="ml-2 block text-sm text-gray-900">
                      Active
                    </label>
                  </div>

                  {/* Preview section */}
                  {values.avatar_url && (
                    <div className="border-t border-gray-200 pt-6">
                      <h3 className="text-lg font-medium text-gray-900">Avatar Preview</h3>
                      <div className="mt-2 flex items-center">
                        <img
                          src={values.avatar_url}
                          alt="Avatar preview"
                          className="h-20 w-20 rounded-full object-cover"
                          onError={(e) => {
                            e.target.onerror = null;
                            e.target.src = "https://via.placeholder.com/80?text=Error";
                          }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex justify-end space-x-3 pt-5">
                    <Link
                      to="/dashboard"
                      className="inline-flex justify-center py-2 px-4 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                    >
                      Cancel
                    </Link>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                    >
                      <FiSave className="mr-2" />
                      {isSubmitting ? 'Saving...' : 'Save Creator'}
                    </button>
                  </div>
                </Form>
              )}
            </Formik>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CreatorForm;
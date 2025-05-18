// src/components/creators/ExamplesManager.jsx
// Component for managing conversation examples for creators

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Formik, Form, Field, FieldArray, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { toast } from 'react-toastify';
import { CreatorService } from '../../services/api.service';
import { FiSave, FiArrowLeft, FiPlus, FiTrash2 } from 'react-icons/fi';

const ExamplesManager = () => {
  const { id } = useParams();
  const [creator, setCreator] = useState(null);
  const [examples, setExamples] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCreator = async () => {
      try {
        setLoading(true);
        const response = await CreatorService.getById(id);
        setCreator(response.creator);
        setExamples(response.creator.examples || []);
      } catch (error) {
        console.error('Error fetching creator:', error);
        toast.error('Failed to load creator data');
      } finally {
        setLoading(false);
      }
    };

    fetchCreator();
  }, [id]);

  // Validation schema for adding a new example
  const validationSchema = Yup.object({
    fan_message: Yup.string().required('Fan message is required'),
    creator_responses: Yup.array()
      .of(Yup.string().required('Response cannot be empty'))
      .min(1, 'At least one response is required')
  });

  // Initial form values
  const initialValues = {
    fan_message: '',
    creator_responses: ['']
  };

  // Handle form submission
  const handleSubmit = async (values, { setSubmitting, resetForm }) => {
    try {
      const response = await CreatorService.addExample(id, values);
      setExamples([...examples, response.example]);
      toast.success('Example added successfully');
      resetForm();
    } catch (error) {
      console.error('Error adding example:', error);
      toast.error(error.response?.data?.message || 'Failed to add example');
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
                <Link to={`/creators/${id}`} className="flex-shrink-0 text-white flex items-center">
                  <FiArrowLeft className="mr-2" />
                  Back to Creator
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <header className="py-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold text-white">
              Style Examples for {creator?.name}
            </h1>
            <p className="mt-2 text-white">
              Add conversation examples to help the AI learn this creator's writing style
            </p>
          </div>
        </header>
      </div>

      {/* Main content */}
      <main className="-mt-32">
        <div className="max-w-7xl mx-auto pb-12 px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow px-5 py-6 sm:px-6">
            {/* Add new example form */}
            <div className="mb-8">
              <h2 className="text-lg font-medium text-gray-900 mb-4">Add New Example</h2>
              
              <Formik
                initialValues={initialValues}
                validationSchema={validationSchema}
                onSubmit={handleSubmit}
              >
                {({ isSubmitting, values }) => (
                  <Form className="space-y-4">
                    <div>
                      <label htmlFor="fan_message" className="block text-sm font-medium text-gray-700 mb-1">
                        Fan Message *
                      </label>
                      <Field
                        as="textarea"
                        id="fan_message"
                        name="fan_message"
                        rows={3}
                        className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                        placeholder="What the fan said..."
                      />
                      <ErrorMessage name="fan_message" component="div" className="mt-1 text-sm text-red-600" />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Creator Responses *
                      </label>
                      <p className="text-xs text-gray-500 mb-2">
                        Add multiple messages if this creator typically breaks responses into separate messages
                      </p>
                      
                      <FieldArray name="creator_responses">
                        {({ remove, push }) => (
                          <div className="space-y-2">
                            {values.creator_responses.map((response, index) => (
                              <div key={index} className="flex items-start">
                                <div className="flex-grow">
                                  <Field
                                    as="textarea"
                                    name={`creator_responses.${index}`}
                                    rows={2}
                                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                                    placeholder={`Creator's message ${index + 1}...`}
                                  />
                                  <ErrorMessage
                                    name={`creator_responses.${index}`}
                                    component="div"
                                    className="mt-1 text-sm text-red-600"
                                  />
                                </div>
                                
                                {values.creator_responses.length > 1 && (
                                  <button
                                    type="button"
                                    className="ml-2 mt-2 text-red-500"
                                    onClick={() => remove(index)}
                                  >
                                    <FiTrash2 />
                                  </button>
                                )}
                              </div>
                            ))}
                            
                            <button
                              type="button"
                              className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                              onClick={() => push('')}
                            >
                              <FiPlus className="mr-1" />
                              Add Another Message
                            </button>
                          </div>
                        )}
                      </FieldArray>
                    </div>
                    
                    <div className="pt-3">
                      <button
                        type="submit"
                        disabled={isSubmitting}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50"
                      >
                        <FiSave className="mr-2" />
                        {isSubmitting ? 'Saving...' : 'Save Example'}
                      </button>
                    </div>
                  </Form>
                )}
              </Formik>
            </div>
            
            {/* Existing examples */}
            <div>
              <h2 className="text-lg font-medium text-gray-900 mb-4">Existing Examples</h2>
              
              {examples.length === 0 ? (
                <div className="bg-gray-50 rounded-lg p-6 text-center">
                  <p className="text-gray-500">No examples added yet</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Add examples above to help the AI learn this creator's writing style
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {examples.map((example, index) => (
                    <div key={example.id || index} className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b">
                        <div className="flex justify-between items-center">
                          <h3 className="text-sm font-medium text-gray-900">Example #{index + 1}</h3>
                          {example.id && (
                            <span className="text-xs text-gray-500">ID: {example.id}</span>
                          )}
                        </div>
                      </div>
                      
                      <div className="p-4">
                        {/* Fan message */}
                        <div className="mb-4">
                          <p className="text-xs font-medium text-gray-500 mb-1">Fan Message:</p>
                          <div className="bg-blue-50 rounded p-3 text-sm">
                            {example.fan_message}
                          </div>
                        </div>
                        
                        {/* Creator responses */}
                        <div>
                          <p className="text-xs font-medium text-gray-500 mb-1">Creator Responses:</p>
                          <div className="space-y-2">
                            {example.creator_responses.map((response, respIndex) => (
                              <div key={respIndex} className="bg-purple-50 rounded p-3 text-sm">
                                {response}
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ExamplesManager;
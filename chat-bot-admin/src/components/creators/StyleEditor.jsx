// src/components/creators/StyleEditor.jsx
// Component for editing creator writing styles

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Formik, Form, Field, FieldArray, ErrorMessage } from 'formik';
import * as Yup from 'yup';
import { toast } from 'react-toastify';
import { CreatorService } from '../../services/api.service';
import { FiSave, FiArrowLeft, FiPlus, FiTrash2 } from 'react-icons/fi';

const StyleEditor = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [creator, setCreator] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
  }, [id, navigate]);

  // Validation schema
  const validationSchema = Yup.object({
    approved_emojis: Yup.array().of(Yup.string()),
    case_style: Yup.string(),
    text_replacements: Yup.object(),
    sentence_separators: Yup.array().of(Yup.string()),
    punctuation_rules: Yup.object(),
    abbreviations: Yup.object(),
    message_length_preference: Yup.string(),
    style_instructions: Yup.string(),
    tone_range: Yup.string()
  });

  // Prepare initial values from creator's style or default values
  const initialValues = {
    approved_emojis: creator?.style?.approved_emojis || ['😊', '👍', '❤️'],
    case_style: creator?.style?.case_style || 'lowercase',
    text_replacements: creator?.style?.text_replacements || { "you": "u", "your": "ur", "you're": "ur" },
    sentence_separators: creator?.style?.sentence_separators || ['emoji', 'new_message'],
    punctuation_rules: creator?.style?.punctuation_rules || { "comma": false, "period": false },
    abbreviations: creator?.style?.abbreviations || { "on my way": "omw", "by the way": "btw" },
    message_length_preference: creator?.style?.message_length_preference || 'short',
    style_instructions: creator?.style?.style_instructions || 'Be friendly and conversational. Use emojis sparingly.',
    tone_range: creator?.style?.tone_range || 'friendly_to_flirty'
  };

  // Handle form submission
  const handleSubmit = async (values, { setSubmitting }) => {
    try {
      await CreatorService.updateStyle(id, values);
      toast.success('Writing style updated successfully');
      navigate(`/creators/${id}`);
    } catch (error) {
      console.error('Error saving style:', error);
      toast.error(error.response?.data?.message || 'Failed to save writing style');
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

  // Helper to transform object to array of key-value pairs for editing
  const objectToArray = (obj) => {
    if (!obj) return [];
    return Object.entries(obj).map(([key, value]) => ({ key, value }));
  };

  // Helper to transform array of key-value pairs back to object
  const arrayToObject = (arr) => {
    return arr.reduce((obj, item) => {
      if (item.key && item.key.trim()) {
        obj[item.key.trim()] = item.value;
      }
      return obj;
    }, {});
  };

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
              Edit Writing Style for {creator?.name}
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
              {({ isSubmitting, values, setFieldValue }) => (
                <Form className="space-y-8">
                  {/* Basic Style Settings */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-4">Basic Style Settings</h2>
                    
                    {/* Case Style */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Case Style
                      </label>
                      <Field
                        as="select"
                        name="case_style"
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      >
                        <option value="lowercase">All Lowercase</option>
                        <option value="sentence_case">Sentence Case</option>
                        <option value="custom">Custom (defined in instructions)</option>
                      </Field>
                    </div>
                    
                    {/* Message Length */}
                    <div className="mb-4">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Message Length Preference
                      </label>
                      <Field
                        as="select"
                        name="message_length_preference"
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      >
                        <option value="short">Short (1-2 sentences)</option>
                        <option value="medium">Medium (2-3 sentences)</option>
                        <option value="match_fan">Match Fan's Length</option>
                      </Field>
                    </div>
                    
                    {/* Tone Range */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Tone Range
                      </label>
                      <Field
                        as="select"
                        name="tone_range"
                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      >
                        <option value="friendly">Friendly Only</option>
                        <option value="friendly_to_flirty">Friendly to Flirty</option>
                        <option value="formal_to_casual">Formal to Casual</option>
                        <option value="professional">Professional</option>
                        <option value="custom">Custom (defined in instructions)</option>
                      </Field>
                    </div>
                  </div>
                  
                  {/* Approved Emojis */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Approved Emojis</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      List the emojis that this creator commonly uses in messages
                    </p>
                    
                    <FieldArray name="approved_emojis">
                      {({ remove, push }) => (
                        <div>
                          {values.approved_emojis && values.approved_emojis.length > 0 ? (
                            <div className="flex flex-wrap gap-2 mb-4">
                              {values.approved_emojis.map((emoji, index) => (
                                <div key={index} className="flex items-center bg-white border rounded-md p-2">
                                  <Field
                                    name={`approved_emojis.${index}`}
                                    className="w-16 border-none focus:ring-0"
                                  />
                                  <button
                                    type="button"
                                    className="ml-2 text-red-500"
                                    onClick={() => remove(index)}
                                  >
                                    <FiTrash2 />
                                  </button>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <div className="mb-4 text-sm text-gray-500">No emojis added yet</div>
                          )}
                          <button
                            type="button"
                            className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                            onClick={() => push('')}
                          >
                            <FiPlus className="mr-1" />
                            Add Emoji
                          </button>
                        </div>
                      )}
                    </FieldArray>
                  </div>
                  
                  {/* Text Replacements */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Text Replacements</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      Words or phrases that should be consistently replaced (e.g., "you" → "u")
                    </p>
                    
                    <FieldArray name="text_replacements_array">
                      {({ remove, push }) => {
                        // Convert to array if not already done
                        if (!values.text_replacements_array) {
                          const replacementsArray = objectToArray(values.text_replacements);
                          setFieldValue('text_replacements_array', replacementsArray);
                        }
                        
                        return (
                          <div>
                            {values.text_replacements_array && values.text_replacements_array.length > 0 ? (
                              <div className="space-y-2 mb-4">
                                {values.text_replacements_array.map((replacement, index) => (
                                  <div key={index} className="flex items-center space-x-2">
                                    <div className="w-1/3">
                                      <Field
                                        name={`text_replacements_array.${index}.key`}
                                        placeholder="Original"
                                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                                        onChange={(e) => {
                                          setFieldValue(`text_replacements_array.${index}.key`, e.target.value);
                                          // Update the main object
                                          const updatedReplacements = arrayToObject(values.text_replacements_array);
                                          setFieldValue('text_replacements', updatedReplacements);
                                        }}
                                      />
                                    </div>
                                    <span>→</span>
                                    <div className="w-1/3">
                                      <Field
                                        name={`text_replacements_array.${index}.value`}
                                        placeholder="Replacement"
                                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                                        onChange={(e) => {
                                          setFieldValue(`text_replacements_array.${index}.value`, e.target.value);
                                          // Update the main object
                                          const updatedReplacements = arrayToObject(values.text_replacements_array);
                                          setFieldValue('text_replacements', updatedReplacements);
                                        }}
                                      />
                                    </div>
                                    <button
                                      type="button"
                                      className="text-red-500"
                                      onClick={() => {
                                        remove(index);
                                        // Update the main object after removal
                                        setTimeout(() => {
                                          const updatedReplacements = arrayToObject(values.text_replacements_array);
                                          setFieldValue('text_replacements', updatedReplacements);
                                        }, 0);
                                      }}
                                    >
                                      <FiTrash2 />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="mb-4 text-sm text-gray-500">No text replacements added yet</div>
                            )}
                            <button
                              type="button"
                              className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                              onClick={() => {
                                push({ key: '', value: '' });
                              }}
                            >
                              <FiPlus className="mr-1" />
                              Add Replacement
                            </button>
                          </div>
                        );
                      }}
                    </FieldArray>
                  </div>
                  
                  {/* Abbreviations */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Abbreviations</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      Common abbreviations used by this creator (e.g., "by the way" → "btw")
                    </p>
                    
                    <FieldArray name="abbreviations_array">
                      {({ remove, push }) => {
                        // Convert to array if not already done
                        if (!values.abbreviations_array) {
                          const abbreviationsArray = objectToArray(values.abbreviations);
                          setFieldValue('abbreviations_array', abbreviationsArray);
                        }
                        
                        return (
                          <div>
                            {values.abbreviations_array && values.abbreviations_array.length > 0 ? (
                              <div className="space-y-2 mb-4">
                                {values.abbreviations_array.map((abbr, index) => (
                                  <div key={index} className="flex items-center space-x-2">
                                    <div className="w-1/3">
                                      <Field
                                        name={`abbreviations_array.${index}.key`}
                                        placeholder="Full phrase"
                                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                                        onChange={(e) => {
                                          setFieldValue(`abbreviations_array.${index}.key`, e.target.value);
                                          // Update the main object
                                          const updatedAbbreviations = arrayToObject(values.abbreviations_array);
                                          setFieldValue('abbreviations', updatedAbbreviations);
                                        }}
                                      />
                                    </div>
                                    <span>→</span>
                                    <div className="w-1/3">
                                      <Field
                                        name={`abbreviations_array.${index}.value`}
                                        placeholder="Abbreviation"
                                        className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                                        onChange={(e) => {
                                          setFieldValue(`abbreviations_array.${index}.value`, e.target.value);
                                          // Update the main object
                                          const updatedAbbreviations = arrayToObject(values.abbreviations_array);
                                          setFieldValue('abbreviations', updatedAbbreviations);
                                        }}
                                      />
                                    </div>
                                    <button
                                      type="button"
                                      className="text-red-500"
                                      onClick={() => {
                                        remove(index);
                                        // Update the main object after removal
                                        setTimeout(() => {
                                          const updatedAbbreviations = arrayToObject(values.abbreviations_array);
                                          setFieldValue('abbreviations', updatedAbbreviations);
                                        }, 0);
                                      }}
                                    >
                                      <FiTrash2 />
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="mb-4 text-sm text-gray-500">No abbreviations added yet</div>
                            )}
                            <button
                              type="button"
                              className="inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                              onClick={() => {
                                push({ key: '', value: '' });
                              }}
                            >
                              <FiPlus className="mr-1" />
                              Add Abbreviation
                            </button>
                          </div>
                        );
                      }}
                    </FieldArray>
                  </div>
                  
                  {/* Punctuation Rules */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Punctuation Rules</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      Special rules for punctuation usage
                    </p>
                    
                    <div className="space-y-3">
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="punctuation_rules.comma"
                          id="comma-rule"
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="comma-rule" className="ml-2 block text-sm text-gray-900">
                          Use commas
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="punctuation_rules.period"
                          id="period-rule"
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="period-rule" className="ml-2 block text-sm text-gray-900">
                          Use periods between sentences
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="punctuation_rules.space_before_punctuation"
                          id="space-rule"
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="space-rule" className="ml-2 block text-sm text-gray-900">
                          Add space before punctuation (e.g., "hello !")
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="punctuation_rules.multiple_exclamation"
                          id="exclamation-rule"
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="exclamation-rule" className="ml-2 block text-sm text-gray-900">
                          Use multiple exclamation/question marks (e.g., "wow!!!")
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  {/* Sentence Separators */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Sentence Separators</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      How this creator separates sentences
                    </p>
                    
                    <div className="space-y-3">
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="has_emoji_separator"
                          id="emoji-separator"
                          checked={values.sentence_separators.includes('emoji')}
                          onChange={(e) => {
                            const updated = e.target.checked
                              ? [...values.sentence_separators, 'emoji']
                              : values.sentence_separators.filter(item => item !== 'emoji');
                            setFieldValue('sentence_separators', updated);
                          }}
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="emoji-separator" className="ml-2 block text-sm text-gray-900">
                          Uses emojis to separate sentences
                        </label>
                      </div>
                      
                      <div className="flex items-center">
                        <Field
                          type="checkbox"
                          name="has_new_message_separator"
                          id="message-separator"
                          checked={values.sentence_separators.includes('new_message')}
                          onChange={(e) => {
                            const updated = e.target.checked
                              ? [...values.sentence_separators, 'new_message']
                              : values.sentence_separators.filter(item => item !== 'new_message');
                            setFieldValue('sentence_separators', updated);
                          }}
                          className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                        />
                        <label htmlFor="message-separator" className="ml-2 block text-sm text-gray-900">
                          Splits into separate messages
                        </label>
                      </div>
                    </div>
                  </div>
                  
                  {/* Style Instructions */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h2 className="text-lg font-medium text-gray-900 mb-2">Detailed Style Instructions</h2>
                    <p className="text-sm text-gray-500 mb-4">
                      Additional instructions or notes about this creator's writing style
                    </p>
                    
                    <Field
                      as="textarea"
                      name="style_instructions"
                      rows={6}
                      className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm"
                      placeholder="Enter detailed writing style instructions here..."
                    />
                    <ErrorMessage name="style_instructions" component="div" className="mt-1 text-sm text-red-600" />
                  </div>
                  
                  <div className="flex justify-end space-x-3 pt-5">
                    <Link
                      to={`/creators/${id}`}
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
                      {isSubmitting ? 'Saving...' : 'Save Style'}
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

export default StyleEditor;
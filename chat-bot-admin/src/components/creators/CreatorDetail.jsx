// src/components/creators/CreatorDetail.jsx
// Component for displaying creator details and writing style

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { CreatorService } from '../../services/api.service';
import { FiArrowLeft, FiEdit2, FiFileText, FiSettings, FiTrash2 } from 'react-icons/fi';

const CreatorDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [creator, setCreator] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

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

  const handleStatusToggle = async () => {
    try {
      await CreatorService.update(id, { active: !creator.active });
      setCreator({ ...creator, active: !creator.active });
      toast.success(`Creator ${creator.active ? 'deactivated' : 'activated'} successfully`);
    } catch (error) {
      console.error('Error toggling status:', error);
      toast.error('Failed to update creator status');
    }
  };

  const handleDelete = async () => {
    if (!deleteConfirm) {
      setDeleteConfirm(true);
      return;
    }

    try {
      await CreatorService.update(id, { active: false });
      toast.success('Creator deactivated successfully');
      navigate('/dashboard');
    } catch (error) {
      console.error('Error deleting creator:', error);
      toast.error('Failed to delete creator');
    }
  };

  // Helper function to format JSON for display
  const formatJson = (jsonObj) => {
    if (!jsonObj) return 'None';
    
    // Convert to entries for display
    return Object.entries(jsonObj).map(([key, value]) => {
      return `${key} → ${value}`;
    }).join(', ');
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
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-white">
                  {creator.name}
                </h1>
                <p className="mt-2 text-white">
                  {creator.description || 'No description'}
                </p>
              </div>
              <div className="flex space-x-2">
                <Link
                  to={`/creators/${id}/edit`}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-700 hover:bg-purple-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  <FiEdit2 className="mr-2" />
                  Edit Profile
                </Link>
                <Link
                  to={`/creators/${id}/style`}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-700 hover:bg-purple-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  <FiSettings className="mr-2" />
                  Edit Style
                </Link>
                <Link
                  to={`/creators/${id}/examples`}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-700 hover:bg-purple-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500"
                >
                  <FiFileText className="mr-2" />
                  Examples
                </Link>
              </div>
            </div>
          </div>
        </header>
      </div>

      {/* Main content */}
      <main className="-mt-32">
        <div className="max-w-7xl mx-auto pb-12 px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow">
            {/* Creator profile */}
            <div className="p-6 border-b">
              <div className="flex items-start justify-between">
                <div className="flex items-center">
                  {creator.avatar_url ? (
                    <img
                      src={creator.avatar_url}
                      alt={creator.name}
                      className="h-16 w-16 rounded-full"
                    />
                  ) : (
                    <div className="h-16 w-16 rounded-full bg-purple-200 flex items-center justify-center">
                      <span className="text-purple-600 font-medium text-lg">
                        {creator.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="ml-4">
                    <h2 className="text-xl font-medium text-gray-900">{creator.name}</h2>
                    <div className="mt-1 flex items-center">
                      <span 
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          creator.active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {creator.active ? 'Active' : 'Inactive'}
                      </span>
                      <button
                        onClick={handleStatusToggle}
                        className="ml-2 text-xs text-purple-600 hover:text-purple-900"
                      >
                        {creator.active ? 'Deactivate' : 'Activate'}
                      </button>
                    </div>
                  </div>
                </div>
                <div>
                  {deleteConfirm ? (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-red-600">Are you sure?</span>
                      <button
                        onClick={handleDelete}
                        className="text-white bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
                      >
                        Yes, deactivate
                      </button>
                      <button
                        onClick={() => setDeleteConfirm(false)}
                        className="text-gray-700 bg-gray-200 hover:bg-gray-300 px-3 py-1 rounded text-sm"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={handleDelete}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-gray-50"
                    >
                      <FiTrash2 className="mr-1" />
                      Deactivate
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Writing style */}
            <div className="p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Writing Style</h3>
              
              {creator.style ? (
                <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Case Style */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Case Style:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.case_style === 'lowercase' ? 'All Lowercase' : 
                       creator.style.case_style === 'sentence_case' ? 'Sentence Case' : 
                       creator.style.case_style || 'Not specified'}
                    </p>
                  </div>
                  
                  {/* Message Length */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Message Length:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.message_length_preference === 'short' ? 'Short (1-2 sentences)' : 
                       creator.style.message_length_preference === 'medium' ? 'Medium (2-3 sentences)' : 
                       creator.style.message_length_preference === 'match_fan' ? 'Match Fan\'s Length' : 
                       creator.style.message_length_preference || 'Not specified'}
                    </p>
                  </div>
                  
                  {/* Tone Range */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Tone Range:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.tone_range === 'friendly' ? 'Friendly Only' : 
                       creator.style.tone_range === 'friendly_to_flirty' ? 'Friendly to Flirty' : 
                       creator.style.tone_range === 'formal_to_casual' ? 'Formal to Casual' : 
                       creator.style.tone_range === 'professional' ? 'Professional' : 
                       creator.style.tone_range || 'Not specified'}
                    </p>
                  </div>
                  
                  {/* Approved Emojis */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Approved Emojis:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.approved_emojis && creator.style.approved_emojis.length > 0 
                        ? creator.style.approved_emojis.join(' ') 
                        : 'None specified'}
                    </p>
                  </div>
                  
                  {/* Text Replacements */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Text Replacements:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.text_replacements 
                        ? formatJson(creator.style.text_replacements)
                        : 'None specified'}
                    </p>
                  </div>
                  
                  {/* Abbreviations */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Abbreviations:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.abbreviations 
                        ? formatJson(creator.style.abbreviations)
                        : 'None specified'}
                    </p>
                  </div>
                  
                  {/* Sentence Separators */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Sentence Separators:</h4>
                    <p className="mt-1 text-sm text-gray-900">
                      {creator.style.sentence_separators && creator.style.sentence_separators.length > 0 
                        ? creator.style.sentence_separators.map(sep => 
                            sep === 'emoji' ? 'Uses emojis' : 
                            sep === 'new_message' ? 'Splits into messages' : sep
                          ).join(', ') 
                        : 'None specified'}
                    </p>
                  </div>
                  
                  {/* Punctuation Rules */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700">Punctuation Rules:</h4>
                    <ul className="mt-1 text-sm text-gray-900 list-disc pl-5">
                      {creator.style.punctuation_rules ? (
                        <>
                          <li>
                            {creator.style.punctuation_rules.comma 
                              ? 'Uses commas' 
                              : 'Avoids commas'}
                          </li>
                          <li>
                            {creator.style.punctuation_rules.period 
                              ? 'Uses periods between sentences' 
                              : 'Avoids periods between sentences'}
                          </li>
                          {creator.style.punctuation_rules.space_before_punctuation && (
                            <li>Adds space before punctuation</li>
                          )}
                          {creator.style.punctuation_rules.multiple_exclamation && (
                            <li>Uses multiple exclamation/question marks</li>
                          )}
                        </>
                      ) : (
                        <li>None specified</li>
                      )}
                    </ul>
                  </div>

                  {/* Style Instructions */}
                  <div className="col-span-1 md:col-span-2">
                    <h4 className="text-sm font-medium text-gray-700">Additional Style Instructions:</h4>
                    <p className="mt-1 text-sm text-gray-900 whitespace-pre-line">
                      {creator.style.style_instructions || 'None specified'}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-6 text-center">
                  <p className="text-gray-500">No writing style defined yet</p>
                  <Link
                    to={`/creators/${id}/style`}
                    className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700"
                  >
                    <FiSettings className="mr-2" />
                    Define Writing Style
                  </Link>
                </div>
              )}
            </div>

            {/* Examples */}
            <div className="p-6 border-t">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Conversation Examples</h3>
                <Link
                  to={`/creators/${id}/examples`}
                  className="inline-flex items-center px-3 py-1 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  <FiFileText className="mr-1" />
                  Manage Examples
                </Link>
              </div>
              
              {creator.examples && creator.examples.length > 0 ? (
                <div className="space-y-4">
                  {creator.examples.slice(0, 2).map((example, index) => (
                    <div key={example.id || index} className="border rounded-lg overflow-hidden">
                      <div className="bg-gray-50 px-4 py-2 border-b">
                        <h3 className="text-sm font-medium text-gray-900">Example #{index + 1}</h3>
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
                  
                  {creator.examples.length > 2 && (
                    <div className="text-center pt-2">
                      <Link 
                        to={`/creators/${id}/examples`}
                        className="text-sm text-purple-600 hover:text-purple-900"
                      >
                        View all {creator.examples.length} examples
                      </Link>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-6 text-center">
                  <p className="text-gray-500">No examples added yet</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Examples help the AI understand this creator's writing style
                  </p>
                  <Link
                    to={`/creators/${id}/examples`}
                    className="mt-3 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700"
                  >
                    <FiPlus className="mr-2" />
                    Add Examples
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CreatorDetail;
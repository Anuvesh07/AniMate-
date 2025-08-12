import React, { useState } from 'react';
import { RotateCcw, Star, Tv, User, AlertCircle, Search, CheckCircle, XCircle } from 'lucide-react';
import axios from 'axios';

const ResultDisplay = ({ result, uploadedImage, onReset }) => {
  const [isReExamining, setIsReExamining] = useState(false);
  const [reExamineHistory, setReExamineHistory] = useState([]);
  const [excludedIds, setExcludedIds] = useState([]);

  const handleReExamine = async (searchType) => {
    setIsReExamining(true);
    
    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8080';
      const currentResult = reExamineHistory.length > 0 ? reExamineHistory[reExamineHistory.length - 1] : result;
      
      let requestData = {
        image_data: uploadedImage,
        search_type: searchType,
        exclude_ids: [...excludedIds],
        focus_ids: []
      };

      if (searchType === 'exclude') {
        // Add current suggestions to excluded list
        const currentSuggestionIds = currentResult.suggestions?.map(s => s.id) || [];
        requestData.exclude_ids = [...excludedIds, ...currentSuggestionIds];
      } else if (searchType === 'focus') {
        // Focus on current suggestions only
        requestData.focus_ids = currentResult.suggestions?.map(s => s.id) || [];
      }

      const response = await axios.post(`${apiUrl}/api/re-examine`, requestData);
      
      if (response.data.success) {
        // Add to history
        setReExamineHistory(prev => [...prev, response.data]);
        
        // Update excluded IDs if we used exclude
        if (searchType === 'exclude') {
          const currentSuggestionIds = currentResult.suggestions?.map(s => s.id) || [];
          setExcludedIds(prev => [...prev, ...currentSuggestionIds]);
        }
      } else {
        // Handle error case
        setReExamineHistory(prev => [...prev, response.data]);
      }
    } catch (error) {
      console.error('Re-examination failed:', error);
      setReExamineHistory(prev => [...prev, {
        success: false,
        error: 'Failed to re-examine image. Please try again.'
      }]);
    } finally {
      setIsReExamining(false);
    }
  };

  const handleBackToStep = (stepIndex) => {
    if (stepIndex === -1) {
      // Back to original
      setReExamineHistory([]);
      setExcludedIds([]);
    } else {
      // Back to specific step
      setReExamineHistory(prev => prev.slice(0, stepIndex + 1));
      // Recalculate excluded IDs up to this step
      // This is simplified - in a real app you'd track this more precisely
    }
  };

  const currentResult = reExamineHistory.length > 0 ? reExamineHistory[reExamineHistory.length - 1] : result;
  const stepNumber = reExamineHistory.length;
  if (!currentResult.success) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-red-500 bg-opacity-20 border border-red-500 rounded-xl p-6 text-center">
          <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-white mb-2">Analysis Failed</h3>
          <p className="text-red-200">{currentResult.error}</p>
          <button
            onClick={onReset}
            className="mt-4 bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header with reset button */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {stepNumber > 0 ? `Re-examination Results (Step ${stepNumber})` : 'Analysis Results'}
          </h2>
          {stepNumber > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {excludedIds.length > 0 && `${excludedIds.length} characters excluded from search`}
            </p>
          )}
        </div>
        <div className="flex space-x-2">
          {stepNumber > 0 && (
            <button
              onClick={() => handleBackToStep(-1)}
              className="flex items-center space-x-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Back to Original</span>
            </button>
          )}
          <button
            onClick={onReset}
            className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <RotateCcw className="h-4 w-4" />
            <span>New Image</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uploaded Image */}
        <div className="bg-white bg-opacity-10 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Your Image</h3>
          <div className="aspect-square bg-gray-800 rounded-lg overflow-hidden">
            <img
              src={uploadedImage}
              alt="Uploaded anime character"
              className="w-full h-full object-contain"
            />
          </div>
        </div>

        {/* Re-examination History */}
        {reExamineHistory.length > 0 && (
          <div className="bg-gray-800 bg-opacity-50 rounded-xl p-4 mb-6">
            <h3 className="text-white font-semibold mb-3">Re-examination History</h3>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleBackToStep(-1)}
                className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                  stepNumber === 0 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-600 hover:bg-gray-500 text-gray-200'
                }`}
              >
                Original
              </button>
              {reExamineHistory.map((_, index) => (
                <button
                  key={index}
                  onClick={() => handleBackToStep(index)}
                  className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                    stepNumber === index + 1
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-600 hover:bg-gray-500 text-gray-200'
                  }`}
                >
                  Step {index + 1}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        <div className="space-y-6">
          {/* Re-examine Options - Always show if we have suggestions */}
          {currentResult.suggestions && currentResult.suggestions.length > 0 && (
            <div className="bg-blue-600 bg-opacity-20 border border-blue-400 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Search className="h-5 w-5 text-blue-400" />
                <h3 className="text-lg font-semibold text-white">Not satisfied with results?</h3>
              </div>
              
              <p className="text-blue-200 mb-4">
                {stepNumber === 0 
                  ? "Help us find better matches by choosing one of these options:"
                  : "Still not satisfied? Continue refining the results:"
                }
              </p>
              
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={() => handleReExamine('focus')}
                  disabled={isReExamining}
                  className="flex items-center justify-center space-x-2 bg-green-600 hover:bg-green-700 disabled:bg-green-800 text-white px-4 py-3 rounded-lg transition-colors flex-1"
                >
                  <CheckCircle className="h-4 w-4" />
                  <span>{isReExamining ? 'Re-examining...' : 'Yes, it\'s one of these'}</span>
                </button>
                
                <button
                  onClick={() => handleReExamine('exclude')}
                  disabled={isReExamining}
                  className="flex items-center justify-center space-x-2 bg-red-600 hover:bg-red-700 disabled:bg-red-800 text-white px-4 py-3 rounded-lg transition-colors flex-1"
                >
                  <XCircle className="h-4 w-4" />
                  <span>{isReExamining ? 'Re-examining...' : 'No, try different characters'}</span>
                </button>
              </div>
              
              {stepNumber > 0 && (
                <div className="mt-3 text-center">
                  <span className="text-blue-300 text-sm">
                    💡 Tip: You can re-examine as many times as you want to find the perfect match!
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Best Match */}
          {currentResult.character && (
            <div className="bg-gradient-to-r from-yellow-500 to-orange-500 bg-opacity-20 border border-yellow-400 rounded-xl p-6">
              <div className="flex items-center space-x-2 mb-4">
                <Star className="h-5 w-5 text-yellow-400" />
                <h3 className="text-lg font-semibold text-white">Best Match</h3>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-yellow-400" />
                  <span className="text-white font-medium">{currentResult.character.name}</span>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Tv className="h-4 w-4 text-yellow-400" />
                  <span className="text-gray-200">{currentResult.character.anime}</span>
                </div>
                
                <p className="text-gray-300 text-sm">{currentResult.character.description}</p>
                
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Confidence:</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-24 bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full"
                        style={{ width: `${currentResult.character.confidence * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-yellow-400 text-sm font-medium">
                      {Math.round(currentResult.character.confidence * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Other Suggestions */}
          {currentResult.suggestions && currentResult.suggestions.length > 0 && (
            <div className="bg-white bg-opacity-10 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Other Possibilities</h3>
              <div className="space-y-3">
                {currentResult.suggestions.slice(0, 3).map((suggestion, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-800 bg-opacity-50 rounded-lg">
                    <div>
                      <div className="text-white font-medium">{suggestion.name}</div>
                      <div className="text-gray-400 text-sm">{suggestion.anime}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-gray-300 text-sm">
                        {Math.round(suggestion.confidence * 100)}%
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No matches found */}
          {!currentResult.character && (!currentResult.suggestions || currentResult.suggestions.length === 0) && (
            <div className="bg-gray-600 bg-opacity-20 border border-gray-500 rounded-xl p-6 text-center">
              <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">No Matches Found</h3>
              <p className="text-gray-300">
                We couldn't identify this character. Try uploading a clearer image or a more popular anime character.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Debug Info (optional) */}
      {currentResult.visionData && (
        <div className="mt-8 bg-gray-800 bg-opacity-50 rounded-xl p-6">
          <details className="text-white">
            <summary className="cursor-pointer font-medium mb-2">Debug Information</summary>
            <div className="text-sm text-gray-300 space-y-2">
              {currentResult.visionData.labels && (
                <div>
                  <strong>Detected Labels:</strong> {currentResult.visionData.labels.join(', ')}
                </div>
              )}
              {currentResult.visionData.texts && (
                <div>
                  <strong>Detected Text:</strong> {currentResult.visionData.texts.join(', ')}
                </div>
              )}
              {currentResult.visionData.web_entities && (
                <div>
                  <strong>Web Entities:</strong> {currentResult.visionData.web_entities.join(', ')}
                </div>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default ResultDisplay;
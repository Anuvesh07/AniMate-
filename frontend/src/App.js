import React, { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import ResultDisplay from './components/ResultDisplay';
import Header from './components/Header';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedImage, setUploadedImage] = useState(null);

  const handleAnalysisComplete = (analysisResult, imageUrl) => {
    setResult(analysisResult);
    setUploadedImage(imageUrl);
    setLoading(false);
  };

  const handleAnalysisStart = () => {
    setLoading(true);
    setResult(null);
  };

  const handleReset = () => {
    setResult(null);
    setUploadedImage(null);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <Header />
      
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {!result && !loading && (
            <ImageUploader 
              onAnalysisStart={handleAnalysisStart}
              onAnalysisComplete={handleAnalysisComplete}
            />
          )}
          
          {loading && (
            <div className="text-center py-20">
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-2 border-white"></div>
              <p className="text-white mt-4 text-lg">Analyzing your image...</p>
            </div>
          )}
          
          {result && (
            <ResultDisplay 
              result={result}
              uploadedImage={uploadedImage}
              onReset={handleReset}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image as ImageIcon } from 'lucide-react';
import axios from 'axios';

const ImageUploader = ({ onAnalysisStart, onAnalysisComplete }) => {
  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    onAnalysisStart();

    try {
      // Convert file to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64Data = e.target.result;
        const imageUrl = base64Data;

        try {
          // Send to backend for analysis
          const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8080';
          const response = await axios.post(`${apiUrl}/api/analyze`, {
            image_data: base64Data
          });

          onAnalysisComplete(response.data, imageUrl);
        } catch (error) {
          console.error('Analysis failed:', error);
          onAnalysisComplete({
            success: false,
            error: 'Failed to analyze image. Please try again.'
          }, imageUrl);
        }
      };
      reader.readAsDataURL(file);
    } catch (error) {
      console.error('File processing failed:', error);
      onAnalysisComplete({
        success: false,
        error: 'Failed to process image file.'
      }, null);
    }
  }, [onAnalysisStart, onAnalysisComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.gif', '.webp']
    },
    multiple: false,
    maxSize: 10 * 1024 * 1024 // 10MB
  });

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
          transition-all duration-300 ease-in-out
          ${isDragActive 
            ? 'border-yellow-400 bg-yellow-400 bg-opacity-10 scale-105' 
            : 'border-gray-400 hover:border-yellow-400 hover:bg-white hover:bg-opacity-5'
          }
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isDragActive ? (
            <Upload className="h-16 w-16 text-yellow-400 animate-bounce" />
          ) : (
            <ImageIcon className="h-16 w-16 text-gray-400" />
          )}
          
          <div className="text-white">
            <h3 className="text-xl font-semibold mb-2">
              {isDragActive ? 'Drop your image here!' : 'Upload an anime image'}
            </h3>
            <p className="text-gray-300">
              Drag & drop an image here, or click to select
            </p>
            <p className="text-sm text-gray-400 mt-2">
              Supports JPG, PNG, GIF, WebP (max 10MB)
            </p>
          </div>
        </div>
      </div>
      
      <div className="mt-8 text-center">
        <h2 className="text-white text-lg font-medium mb-4">How it works:</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="text-yellow-400 font-semibold">1. Upload</div>
            <div className="text-gray-300">Choose an anime character image</div>
          </div>
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="text-yellow-400 font-semibold">2. Analyze</div>
            <div className="text-gray-300">AI processes the image</div>
          </div>
          <div className="bg-white bg-opacity-10 rounded-lg p-4">
            <div className="text-yellow-400 font-semibold">3. Discover</div>
            <div className="text-gray-300">Get character identification</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageUploader;
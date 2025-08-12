import React from 'react';
import { Sparkles } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-black bg-opacity-20 backdrop-blur-sm border-b border-white border-opacity-10">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-center space-x-3">
          <Sparkles className="h-8 w-8 text-yellow-400" />
          <h1 className="text-3xl font-bold text-white">
            Anime Guesser
          </h1>
          <Sparkles className="h-8 w-8 text-yellow-400" />
        </div>
        <p className="text-center text-gray-300 mt-2">
          Upload an anime image and let AI identify the character!
        </p>
      </div>
    </header>
  );
};

export default Header;
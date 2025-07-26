import React from 'react';
import { useStore } from '../store/useStore';

export const ChapterSelector: React.FC = () => {
  const { selectedBook, selectedChapter, setSelectedChapter } = useStore();

  if (!selectedBook) return null;

  return (
    <div className="p-4 border-b border-gray-200">
      <h3 className="text-sm font-medium text-gray-600 mb-2">
        {selectedBook.name} - Select Chapter
      </h3>
      <div className="grid grid-cols-10 gap-1">
        {Array.from({ length: selectedBook.chapters }, (_, i) => i + 1).map((chapter) => (
          <button
            key={chapter}
            onClick={() => setSelectedChapter(chapter)}
            className={`text-sm p-2 rounded transition-colors ${
              selectedChapter === chapter
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {chapter}
          </button>
        ))}
      </div>
    </div>
  );
};
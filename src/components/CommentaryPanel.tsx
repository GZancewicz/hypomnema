import React from 'react';
import { useStore } from '../store/useStore';

export const CommentaryPanel: React.FC = () => {
  const { showCommentaryPanel, selectedCommentary, toggleCommentaryPanel } = useStore();

  if (!showCommentaryPanel) return null;

  return (
    <div className="w-96 bg-gray-50 border-l border-gray-200 p-6 overflow-y-auto">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Commentary</h3>
        <button
          onClick={toggleCommentaryPanel}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>
      
      {selectedCommentary ? (
        <div>
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600">Verse</p>
            <p className="text-lg">{selectedCommentary.verseRef}</p>
          </div>
          
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600">Author</p>
            <p className="text-lg">{selectedCommentary.author}</p>
          </div>
          
          {selectedCommentary.source && (
            <div className="mb-4">
              <p className="text-sm font-medium text-gray-600">Source</p>
              <p className="text-sm italic">{selectedCommentary.source}</p>
            </div>
          )}
          
          <div className="mb-4">
            <p className="text-sm font-medium text-gray-600 mb-2">Commentary</p>
            <p className="leading-relaxed">{selectedCommentary.text}</p>
          </div>
        </div>
      ) : (
        <p className="text-gray-500">Select a verse with commentary to view</p>
      )}
    </div>
  );
};
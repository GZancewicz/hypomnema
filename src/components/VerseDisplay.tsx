import React, { useState } from 'react';
import { useStore } from '../store/useStore';
import { Commentary } from '../types';

// Sample commentary data - in a real app, this would come from an API
const sampleCommentaries: Commentary[] = [
  {
    id: '1',
    verseRef: 'John 1:1',
    author: 'Chrysostom',
    text: 'In the beginning was the Word. If He was in the beginning, and was with God, the Father was not alone.',
    source: 'Homilies on John, Homily II'
  },
  {
    id: '2',
    verseRef: 'John 1:1',
    author: 'Cyril of Alexandria',
    text: 'The Word was in the beginning, that is, always existed, being eternally with God.',
    source: 'Commentary on John, Book I'
  }
];

// Sample verse data - in a real app, this would come from an API
const sampleVerses = [
  { verse: 1, text: 'In the beginning was the Word, and the Word was with God, and the Word was God.' },
  { verse: 2, text: 'The same was in the beginning with God.' },
  { verse: 3, text: 'All things were made by him; and without him was not any thing made that was made.' },
  { verse: 4, text: 'In him was life; and the life was the light of men.' },
  { verse: 5, text: 'And the light shineth in darkness; and the darkness comprehended it not.' },
];

export const VerseDisplay: React.FC = () => {
  const { selectedBook, selectedChapter, setHoveredVerse, setSelectedCommentary } = useStore();
  const [hoveredVerseNum, setHoveredVerseNum] = useState<number | null>(null);

  if (!selectedBook) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center text-gray-500">
        Select a book to begin reading
      </div>
    );
  }

  const getCommentariesForVerse = (verseNum: number) => {
    const verseRef = `${selectedBook.name} ${selectedChapter}:${verseNum}`;
    return sampleCommentaries.filter(c => c.verseRef === verseRef);
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <h2 className="text-2xl font-bold mb-6">
        {selectedBook.name} {selectedChapter}
      </h2>
      
      <div className="space-y-4 max-w-3xl">
        {sampleVerses.map((verse) => {
          const commentaries = getCommentariesForVerse(verse.verse);
          const hasCommentary = commentaries.length > 0;
          
          return (
            <div
              key={verse.verse}
              className="relative group"
              onMouseEnter={() => {
                setHoveredVerseNum(verse.verse);
                setHoveredVerse(`${selectedBook.name} ${selectedChapter}:${verse.verse}`);
              }}
              onMouseLeave={() => {
                setHoveredVerseNum(null);
                setHoveredVerse(null);
              }}
            >
              <p className={`text-lg leading-relaxed transition-colors ${
                hasCommentary ? 'hover:bg-blue-50 cursor-pointer' : ''
              } p-2 rounded`}>
                <span className="font-semibold text-gray-600 mr-2">{verse.verse}</span>
                <span className="text-gray-800">{verse.text}</span>
              </p>
              
              {hasCommentary && hoveredVerseNum === verse.verse && (
                <div className="absolute left-0 top-full mt-1 bg-white shadow-lg rounded-lg p-3 z-10 border border-gray-200">
                  <p className="text-sm font-medium text-gray-600 mb-2">Commentary available from:</p>
                  {commentaries.map((commentary) => (
                    <button
                      key={commentary.id}
                      onClick={() => setSelectedCommentary(commentary)}
                      className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 py-1"
                    >
                      • {commentary.author}
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
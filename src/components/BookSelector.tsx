import React from 'react';
import { books } from '../data/books';
import { useStore } from '../store/useStore';

export const BookSelector: React.FC = () => {
  const { selectedBook, setSelectedBook } = useStore();

  return (
    <div className="p-4 border-b border-gray-200">
      <h2 className="text-lg font-semibold mb-4">Select Book</h2>
      
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-600 mb-2">Old Testament</h3>
        <div className="grid grid-cols-3 gap-2">
          {books.filter(b => b.testament === 'OT' && !b.isDeuterocanonical).map((book) => (
            <button
              key={book.name}
              onClick={() => setSelectedBook(book)}
              className={`text-sm p-2 rounded transition-colors ${
                selectedBook?.name === book.name
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              {book.name}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-600 mb-2">Deuterocanon</h3>
        <div className="grid grid-cols-3 gap-2">
          {books.filter(b => b.isDeuterocanonical).map((book) => (
            <button
              key={book.name}
              onClick={() => setSelectedBook(book)}
              className={`text-sm p-2 rounded transition-colors ${
                selectedBook?.name === book.name
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              {book.name}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-600 mb-2">New Testament</h3>
        <div className="grid grid-cols-3 gap-2">
          {books.filter(b => b.testament === 'NT').map((book) => (
            <button
              key={book.name}
              onClick={() => setSelectedBook(book)}
              className={`text-sm p-2 rounded transition-colors ${
                selectedBook?.name === book.name
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
              }`}
            >
              {book.name}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
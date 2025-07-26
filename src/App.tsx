import React from 'react';
import { BookSelector } from './components/BookSelector';
import { ChapterSelector } from './components/ChapterSelector';
import { VerseDisplay } from './components/VerseDisplay';
import { CommentaryPanel } from './components/CommentaryPanel';

function App() {
  return (
    <div className="flex h-screen bg-white">
      <aside className="w-80 bg-gray-50 border-r border-gray-200 overflow-y-auto">
        <h1 className="text-2xl font-bold p-4 border-b border-gray-200">Hypomnema</h1>
        <BookSelector />
        <ChapterSelector />
      </aside>
      
      <main className="flex flex-1">
        <VerseDisplay />
        <CommentaryPanel />
      </main>
    </div>
  );
}

export default App;
import { create } from 'zustand';
import { Book, Commentary } from '../types';

interface BibleStore {
  selectedBook: Book | null;
  selectedChapter: number;
  showCommentaryPanel: boolean;
  selectedCommentary: Commentary | null;
  hoveredVerse: string | null;
  
  setSelectedBook: (book: Book) => void;
  setSelectedChapter: (chapter: number) => void;
  toggleCommentaryPanel: () => void;
  setSelectedCommentary: (commentary: Commentary | null) => void;
  setHoveredVerse: (verseRef: string | null) => void;
}

export const useStore = create<BibleStore>((set) => ({
  selectedBook: null,
  selectedChapter: 1,
  showCommentaryPanel: false,
  selectedCommentary: null,
  hoveredVerse: null,
  
  setSelectedBook: (book) => set({ selectedBook: book, selectedChapter: 1 }),
  setSelectedChapter: (chapter) => set({ selectedChapter: chapter }),
  toggleCommentaryPanel: () => set((state) => ({ showCommentaryPanel: !state.showCommentaryPanel })),
  setSelectedCommentary: (commentary) => set({ selectedCommentary: commentary, showCommentaryPanel: true }),
  setHoveredVerse: (verseRef) => set({ hoveredVerse: verseRef }),
}));
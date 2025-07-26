export interface Verse {
  book: string;
  chapter: number;
  verse: number;
  text: string;
  greekText?: string;
}

export interface Commentary {
  id: string;
  verseRef: string;
  author: 'Chrysostom' | 'Cyril of Alexandria';
  text: string;
  source?: string;
}

export interface Book {
  name: string;
  chapters: number;
  testament: 'OT' | 'NT';
  isDeuterocanonical?: boolean;
}
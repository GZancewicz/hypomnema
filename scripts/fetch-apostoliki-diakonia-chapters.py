#!/usr/bin/env python3
import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json

class GreekChapterParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.verses = []
        self.current_verse = None
        self.current_text = []
        self.in_verse_num = False
        self.in_content = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'font':
            for attr, value in attrs:
                if attr == 'color' and value == '#0000ff':
                    self.in_verse_num = True
                    
    def handle_endtag(self, tag):
        if tag == 'font' and self.in_verse_num:
            self.in_verse_num = False
            
    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
            
        # Check for verse numbers (usually in blue font)
        if self.in_verse_num and text.isdigit():
            # Save previous verse if exists
            if self.current_verse and self.current_text:
                verse_text = ' '.join(self.current_text).strip()
                if verse_text and any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in verse_text):
                    self.verses.append((self.current_verse, verse_text))
            
            # Start new verse
            self.current_verse = int(text)
            self.current_text = []
            self.in_content = True
        
        # Collect verse text
        elif self.in_content and self.current_verse:
            # Check if it contains Greek characters
            if any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in text):
                self.current_text.append(text)
    
    def get_verses(self):
        # Don't forget the last verse
        if self.current_verse and self.current_text:
            verse_text = ' '.join(self.current_text).strip()
            if verse_text and any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in verse_text):
                self.verses.append((self.current_verse, verse_text))
        
        return self.verses

def get_book_info():
    """Return book information including sequence numbers and chapter counts"""
    return {
        'Levitikon': {'seq': 3, 'chapters': 27},
        'Arithmoi': {'seq': 4, 'chapters': 36},
        'Defteronomion': {'seq': 5, 'chapters': 34},
        'Navi': {'seq': 6, 'chapters': 24},
        'Kritai': {'seq': 7, 'chapters': 21},
        'Routh': {'seq': 8, 'chapters': 4},
        'Neemias': {'seq': 17, 'chapters': 13},
        'Tovit': {'seq': 18, 'chapters': 14},
        'Ioudith': {'seq': 19, 'chapters': 16},
        'Esthir': {'seq': 20, 'chapters': 10},
        'Psalmoi': {'seq': 24, 'chapters': 151},
        'Iov': {'seq': 25, 'chapters': 42},
        'Parimiai': {'seq': 26, 'chapters': 31},
        'Ekklhsiastis': {'seq': 27, 'chapters': 12},
        'Asma_Asmaton': {'seq': 28, 'chapters': 8},
        'Sofia': {'seq': 29, 'chapters': 19},
        'Sofia_Sirah': {'seq': 30, 'chapters': 51},
        'Osie': {'seq': 31, 'chapters': 14},
        'Amos': {'seq': 32, 'chapters': 9},
        'Miheas': {'seq': 33, 'chapters': 7},
        'Iohl': {'seq': 34, 'chapters': 3},
        'Ovdiou': {'seq': 35, 'chapters': 1},
        'Ionas': {'seq': 36, 'chapters': 4},
        'Naoum': {'seq': 37, 'chapters': 3},
        'Amvakoum': {'seq': 38, 'chapters': 3},
        'Sofonias': {'seq': 39, 'chapters': 3},
        'Aggaios': {'seq': 40, 'chapters': 2},
        'Zaharias': {'seq': 41, 'chapters': 14},
        'Malahias': {'seq': 42, 'chapters': 4},
        'Hsaias': {'seq': 43, 'chapters': 66},
        'Ieremias': {'seq': 44, 'chapters': 52},
        'Varouh': {'seq': 45, 'chapters': 5},
        'Thrinoi': {'seq': 46, 'chapters': 5},
        'Epistoli_Ier': {'seq': 47, 'chapters': 1},
        'Iezekihl': {'seq': 48, 'chapters': 48},
        'Danihl': {'seq': 49, 'chapters': 12}
    }

def fetch_chapter(book_name, book_seq, chapter_num, max_retries=3):
    """Fetch a complete chapter from the website"""
    # Handle main parameter
    main_param = book_name.lower()
    if book_name == 'Parimiai':
        main_param = 'parimiai'
    elif book_name == 'Sofia_Sirah':
        main_param = 'sofia_sirah'
    elif book_name == 'Asma_Asmaton':
        main_param = 'asma_asmaton'
    elif book_name == 'Epistoli_Ier':
        main_param = 'epistoli_ier'
    
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={main_param}&file={book_seq}.{chapter_num}.htm"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
            req.add_header('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
            
            with urllib.request.urlopen(req, timeout=15) as response:
                raw_data = response.read()
                
                # Try ISO-8859-7 first (Greek encoding)
                try:
                    content = raw_data.decode('iso-8859-7')
                except:
                    content = raw_data.decode('utf-8', errors='ignore')
                
                # Parse the chapter
                parser = GreekChapterParser()
                parser.feed(content)
                verses = parser.get_verses()
                
                return verses
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            elif e.code == 500:
                # Server error - wait longer before retry
                if attempt < max_retries - 1:
                    time.sleep(5)
                continue
            else:
                print(f"HTTP Error {e.code}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            print(f"Error: {e}")
            return None
    
    return None

def load_progress():
    """Load fetch progress from JSON file"""
    progress_file = 'apostoliki_chapter_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save fetch progress to JSON file"""
    progress_file = 'apostoliki_chapter_progress.json'
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def fetch_books_by_chapter():
    """Fetch books chapter by chapter"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'apostoliki_diakonia')
    
    book_info = get_book_info()
    progress = load_progress()
    
    # Determine which books to fetch
    existing_folders = set(os.listdir(base_dir)) if os.path.exists(base_dir) else set()
    missing_books = []
    
    for book_name, info in book_info.items():
        if book_name not in existing_folders:
            missing_books.append((book_name, info['seq'], info['chapters']))
    
    print(f"Found {len(missing_books)} books to fetch")
    print("=" * 60)
    
    for book_name, book_seq, max_chapters in sorted(missing_books, key=lambda x: x[1]):
        # Skip if already completed
        if book_name in progress and progress[book_name].get('status') == 'completed':
            print(f"Skipping {book_name} - already completed")
            continue
            
        print(f"\nFetching {book_name} (seq: {book_seq}, chapters: {max_chapters})...")
        
        book_dir = os.path.join(base_dir, book_name)
        os.makedirs(book_dir, exist_ok=True)
        
        chapters_found = 0
        start_time = time.time()
        
        try:
            for chapter in range(1, max_chapters + 1):
                print(f"  Chapter {chapter}/{max_chapters}: ", end='', flush=True)
                
                verses = fetch_chapter(book_name, book_seq, chapter)
                
                if verses:
                    # Create chapter directory
                    chapter_dir = os.path.join(book_dir, str(chapter))
                    os.makedirs(chapter_dir, exist_ok=True)
                    
                    # Save each verse
                    for verse_num, verse_text in verses:
                        verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                        with open(verse_file, 'w', encoding='utf-8') as f:
                            f.write(verse_text)
                    
                    print(f"✓ ({len(verses)} verses)")
                    chapters_found += 1
                else:
                    print("✗ (no verses found)")
                    # For single-chapter books, this might be OK
                    if max_chapters == 1:
                        break
                
                # Rate limiting
                time.sleep(2)
            
            # Update progress
            if chapters_found > 0:
                progress[book_name] = {
                    'status': 'completed',
                    'chapters_found': chapters_found,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                print(f"  ✓ Completed {book_name}: {chapters_found}/{max_chapters} chapters")
            else:
                progress[book_name] = {
                    'status': 'failed',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                print(f"  ✗ Failed to fetch {book_name}")
                
            save_progress(progress)
            
            # Wait between books
            time.sleep(5)
                
        except KeyboardInterrupt:
            print(f"\n  ⚠ Interrupted while fetching {book_name}")
            progress[book_name] = {
                'status': 'interrupted',
                'chapters_found': chapters_found,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            save_progress(progress)
            raise
        except Exception as e:
            print(f"\n  ✗ Error fetching {book_name}: {e}")
            progress[book_name] = {
                'status': 'error',
                'error': str(e),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            save_progress(progress)

def main():
    print("Fetching Books from apostoliki-diakonia.gr (Chapter Method)")
    print("=" * 60)
    fetch_books_by_chapter()

if __name__ == "__main__":
    main()
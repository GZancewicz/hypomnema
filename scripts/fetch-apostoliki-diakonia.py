#!/usr/bin/env python3
import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json

class GreekBibleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.td_count = 0
        self.text_parts = []
        self.found_content = False
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
            self.td_count += 1
            
    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False
            
    def handle_data(self, data):
        if self.in_td and self.td_count > 10:  # Skip header TDs
            text = data.strip()
            # Look for Greek text patterns
            if text and len(text) > 20 and not text.startswith('<'):
                # Check if it contains Greek characters
                if any('\u0370' <= char <= '\u03ff' or '\u1f00' <= char <= '\u1fff' for char in text):
                    self.text_parts.append(text)
                    self.found_content = True

def get_book_info():
    """Return book information including sequence numbers and chapter counts"""
    return {
        'Genesis': {'seq': 1, 'chapters': 50},
        'Exodos': {'seq': 2, 'chapters': 40},
        'Levitikon': {'seq': 3, 'chapters': 27},
        'Arithmoi': {'seq': 4, 'chapters': 36},
        'Defteronomion': {'seq': 5, 'chapters': 34},
        'Navi': {'seq': 6, 'chapters': 24},
        'Kritai': {'seq': 7, 'chapters': 21},
        'Routh': {'seq': 8, 'chapters': 4},
        'VasilionA': {'seq': 9, 'chapters': 31},
        'VasilionB': {'seq': 10, 'chapters': 24},
        'VasilionG': {'seq': 11, 'chapters': 22},
        'VasilionD': {'seq': 12, 'chapters': 25},
        'ParalipomenonA': {'seq': 13, 'chapters': 29},
        'ParalipomenonB': {'seq': 14, 'chapters': 36},
        'EsdrasA': {'seq': 15, 'chapters': 10},
        'EsdrasB': {'seq': 16, 'chapters': 10},
        'Neemias': {'seq': 17, 'chapters': 13},
        'Tovit': {'seq': 18, 'chapters': 14},
        'Ioudith': {'seq': 19, 'chapters': 16},
        'Esthir': {'seq': 20, 'chapters': 10},
        'MakkavaionA': {'seq': 21, 'chapters': 16},
        'MakkavaionB': {'seq': 22, 'chapters': 15},
        'makkavaionG': {'seq': 23, 'chapters': 7},
        'Psalmoi': {'seq': 24, 'chapters': 151},  # Psalms has 151 in LXX
        'Iov': {'seq': 25, 'chapters': 42},
        'Parimiai': {'seq': 26, 'chapters': 31},  # Proverbs
        'Ekklhsiastis': {'seq': 27, 'chapters': 12},
        'Asma_Asmaton': {'seq': 28, 'chapters': 8},
        'Sofia': {'seq': 29, 'chapters': 19},  # Wisdom of Solomon
        'Sofia_Sirah': {'seq': 30, 'chapters': 51},  # Sirach
        'Osie': {'seq': 31, 'chapters': 14},
        'Amos': {'seq': 32, 'chapters': 9},
        'Miheas': {'seq': 33, 'chapters': 7},
        'Iohl': {'seq': 34, 'chapters': 3},
        'Ovdiou': {'seq': 35, 'chapters': 1},  # Obadiah - single chapter
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
        'Epistoli_Ier': {'seq': 47, 'chapters': 1},  # Letter of Jeremiah - single chapter
        'Iezekihl': {'seq': 48, 'chapters': 48},
        'Danihl': {'seq': 49, 'chapters': 12},
        'makkavaionD': {'seq': 50, 'chapters': 18}
    }

def fetch_verse_with_encoding(url_name, book_seq, chapter, verse, max_retries=3):
    """Fetch a verse handling ISO-8859-7 encoding"""
    # Handle main parameter mapping
    main_param = url_name.lower()
    if url_name.startswith('Vasilion'):
        main_param = 'vasilion' + url_name[-1].lower()
    elif url_name.startswith('Paralipomenon'):
        main_param = 'paralipomenon' + url_name[-1].lower()
    elif url_name.startswith('Esdras'):
        main_param = 'esdras' + url_name[-1].lower()
    elif url_name.startswith('Makkavaion'):
        main_param = 'makkavaion' + url_name[-1].lower()
    elif url_name == 'Parimiai':
        main_param = 'parimiai'
    elif url_name == 'Sofia_Sirah':
        main_param = 'sofia_sirah'
    elif url_name == 'Asma_Asmaton':
        main_param = 'asma_asmaton'
    elif url_name == 'Epistoli_Ier':
        main_param = 'epistoli_ier'
    
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{url_name}.asp&main={main_param}&file={book_seq}.{chapter}.{verse}.htm"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                raw_data = response.read()
                
                try:
                    content = raw_data.decode('iso-8859-7')
                except:
                    content = raw_data.decode('utf-8', errors='ignore')
                
                return content
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            elif e.code == 500 and attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return None
    
    return None

def extract_greek_text(html_content):
    """Extract Greek text from HTML content"""
    if not html_content:
        return None
        
    parser = GreekBibleParser()
    parser.feed(html_content)
    
    if parser.text_parts:
        full_text = ' '.join(parser.text_parts)
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = re.sub(r'<[^>]+>', '', full_text)
        full_text = re.sub(r'^\d+\s*', '', full_text)
        
        return full_text.strip()
    
    return None

def fetch_chapter(folder_name, url_name, book_seq, chapter_num, max_verses=80):
    """Fetch a chapter with progress indication"""
    verses = []
    consecutive_failures = 0
    verse_num = 1
    
    while verse_num <= max_verses and consecutive_failures < 5:
        content = fetch_verse_with_encoding(url_name, book_seq, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
                consecutive_failures = 0
                print(f".", end='', flush=True)
            else:
                consecutive_failures += 1
        else:
            consecutive_failures += 1
            
            # For single-chapter books or if we haven't found any verses yet
            if not verses and consecutive_failures >= 5:
                break
        
        verse_num += 1
        time.sleep(0.5)  # Be polite to the server
    
    return verses

def load_progress():
    """Load fetch progress from JSON file"""
    progress_file = 'apostoliki_fetch_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save fetch progress to JSON file"""
    progress_file = 'apostoliki_fetch_progress.json'
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)

def fetch_missing_books():
    """Fetch missing books from apostoliki-diakonia.gr"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'apostoliki_diakonia')
    
    book_info = get_book_info()
    progress = load_progress()
    
    # Determine which books to fetch
    existing_folders = set(os.listdir(base_dir)) if os.path.exists(base_dir) else set()
    missing_books = []
    
    for book_name, info in book_info.items():
        if book_name not in existing_folders or book_name in progress.get('retry', []):
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
                
                verses = fetch_chapter(book_name, book_name, book_seq, chapter)
                
                if verses:
                    # Create chapter directory
                    chapter_dir = os.path.join(book_dir, str(chapter))
                    os.makedirs(chapter_dir, exist_ok=True)
                    
                    # Save each verse
                    for verse_text in verses:
                        match = re.match(r'^(\d+):(\d+)\s+(.+)$', verse_text)
                        if match:
                            verse_num = match.group(2)
                            text = match.group(3)
                            verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                            with open(verse_file, 'w', encoding='utf-8') as f:
                                f.write(text)
                    
                    print(f" ✓ ({len(verses)} verses)")
                    chapters_found += 1
                else:
                    print(" ✗ (no verses found)")
                    # For single-chapter books, this might be expected
                    if max_chapters == 1:
                        break
            
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
            
            # Rate limiting between books
            elapsed = time.time() - start_time
            if elapsed < 30:  # If book took less than 30 seconds, wait a bit
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
    print("Fetching Books from apostoliki-diakonia.gr")
    print("=" * 60)
    fetch_missing_books()

if __name__ == "__main__":
    main()
import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json

class ChapterParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.content_started = False
        self.chapter_text = []
        self.in_td = False
        self.td_count = 0
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
            self.td_count += 1
            # Look for the main content TD
            for attr, value in attrs:
                if attr == 'width' and value == '560':
                    self.in_content = True
                    
    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False
            
    def handle_data(self, data):
        if self.in_content and self.in_td:
            text = data.strip()
            # Look for verse patterns (number followed by text)
            if text and not text.startswith('Κεφάλαιο'):
                # Check if it contains Greek text
                if any('\u0370' <= char <= '\u03ff' or '\u1f00' <= char <= '\u1fff' for char in text):
                    self.chapter_text.append(text)

def fetch_chapter_page(book_url_name, book_seq_num, chapter, main_param):
    """Fetch a chapter page"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_url_name}.asp&main={main_param}&file={book_seq_num}.{chapter}.htm"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = response.read()
            
            # Decode as ISO-8859-7
            try:
                content = raw_data.decode('iso-8859-7')
            except:
                content = raw_data.decode('utf-8', errors='ignore')
            
            return content
            
    except Exception as e:
        print(f"    Error fetching: {e}")
        return None

def parse_chapter_content(html_content):
    """Parse the chapter content into verses"""
    if not html_content:
        return []
    
    parser = ChapterParser()
    parser.feed(html_content)
    
    verses = []
    if parser.chapter_text:
        # Join all text and look for verse patterns
        full_text = ' '.join(parser.chapter_text)
        
        # Pattern: number followed by text until next number or end
        # More flexible pattern to handle various formats
        parts = re.split(r'(\d+)\s*', full_text)
        
        current_verse = None
        for i, part in enumerate(parts):
            if part.isdigit() and i + 1 < len(parts):
                verse_num = int(part)
                verse_text = parts[i + 1].strip()
                if verse_text and len(verse_text) > 5:
                    verses.append((verse_num, verse_text))
    
    return verses

def fetch_book_with_chapters(book_folder, book_info, max_chapters):
    """Fetch a book that uses chapter-level pages"""
    url_name = book_info['url_name']
    greek_name = book_info['greek_name']
    
    # Get sequence number
    book_sequences = {
        'vasiliona': (9, 'vasilionA'),
        'vasilionb': (10, 'vasilionB'),
        'vasiliong': (11, 'vasilionG'),
        'vasiliond': (12, 'vasilionD'),
        'paralipomenona': (13, 'paralipomenonA'),
        'paralipomenonb': (14, 'paralipomenonB'),
        'esdrasa': (15, 'esdrasA'),
        'esdrasb': (16, 'esdrasB'),
        'makkavaiona': (21, 'makkavaionA'),
        'makkavaionb': (22, 'makkavaionB'),
        'makkavaiong': (23, 'makkavaionG'),
        'makkavaiond': (50, 'makkavaionD')
    }
    
    if book_folder not in book_sequences:
        print(f"Unknown book sequence for {book_folder}")
        return False
    
    book_seq, main_param = book_sequences[book_folder]
    
    print(f"\nFetching {greek_name} (#{book_seq})")
    print(f"Folder: {book_folder}")
    print(f"URL name: {url_name}")
    print(f"Main param: {main_param}")
    print("=" * 50)
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint', book_folder)
    os.makedirs(base_dir, exist_ok=True)
    
    chapters_found = 0
    consecutive_failures = 0
    
    for chapter in range(1, max_chapters + 1):
        print(f"Chapter {chapter}: ", end='', flush=True)
        
        # Fetch the chapter page
        content = fetch_chapter_page(url_name, book_seq, chapter, main_param)
        
        if content:
            verses = parse_chapter_content(content)
            
            if verses:
                # Create chapter directory
                chapter_dir = os.path.join(base_dir, str(chapter))
                os.makedirs(chapter_dir, exist_ok=True)
                
                # Save each verse
                for verse_num, verse_text in verses:
                    verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                    with open(verse_file, 'w', encoding='utf-8') as f:
                        f.write(verse_text)
                
                print(f"✓ ({len(verses)} verses)")
                chapters_found += 1
                consecutive_failures = 0
            else:
                print("✗ (no verses found)")
                consecutive_failures += 1
        else:
            print("✗ (fetch failed)")
            consecutive_failures += 1
        
        # Stop if we get too many failures in a row
        if consecutive_failures >= 3 and chapters_found > 0:
            print("\nNo more chapters found")
            break
        
        time.sleep(0.5)
    
    if chapters_found > 0:
        print(f"\n✓ Successfully fetched {chapters_found} chapters of {greek_name}")
        return True
    else:
        print(f"\n✗ Failed to fetch any chapters of {greek_name}")
        return False

def main():
    import sys
    
    # Load book mapping
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    if len(sys.argv) < 2:
        print("Usage: python fetch-septuagint-chapters.py <book_folder> [max_chapters]")
        print("\nBooks that need chapter-level fetching:")
        special_books = ['vasiliona', 'vasilionb', 'vasiliong', 'vasiliond',
                        'paralipomenona', 'paralipomenonb', 'esdrasa', 'esdrasb',
                        'makkavaiona', 'makkavaionb', 'makkavaiong', 'makkavaiond']
        for book in special_books:
            if book in mapping:
                print(f"  {book} - {mapping[book]['greek_name']}")
        return
    
    book_folder = sys.argv[1]
    max_chapters = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    if book_folder not in mapping:
        print(f"Unknown book: {book_folder}")
        return
    
    fetch_book_with_chapters(book_folder, mapping[book_folder], max_chapters)

if __name__ == "__main__":
    main()
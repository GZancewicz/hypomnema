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

def get_book_sequence_numbers():
    """Return the sequence numbers for each book based on the order in the site"""
    return {
        'genesis': 1,
        'exodos': 2,
        'levitikon': 3,
        'arithmoi': 4,
        'defteronomion': 5,
        'navi': 6,
        'kritai': 7,
        'routh': 8,
        'vasiliona': 9,
        'vasilionb': 10,
        'vasiliong': 11,
        'vasiliond': 12,
        'paralipomenona': 13,
        'paralipomenonb': 14,
        'esdrasa': 15,
        'esdrasb': 16,
        'neemias': 17,
        'tovit': 18,
        'ioudith': 19,
        'esthir': 20,
        'makkavaiona': 21,
        'makkavaionb': 22,
        'makkavaiong': 23,
        'psalmoi': 24,
        'iov': 25,
        'parimiai': 26,
        'ekklhsiastis': 27,
        'asma_asmaton': 28,
        'sofia': 29,
        'sofia_sirah': 30,
        'osie': 31,
        'amos': 32,
        'miheas': 33,
        'iohl': 34,
        'ovdiou': 35,
        'ionas': 36,
        'naoum': 37,
        'amvakoum': 38,
        'sofonias': 39,
        'aggaios': 40,
        'zaharias': 41,
        'malahias': 42,
        'hsaias': 43,
        'ieremias': 44,
        'varouh': 45,
        'thrinoi': 46,
        'epistoli_ier': 47,
        'iezekihl': 48,
        'danihl': 49,
        'makkavaiond': 50
    }

def fetch_chapter_text(book_url_name, book_seq_num, chapter, max_retries=2):
    """Fetch an entire chapter using the correct URL pattern"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_url_name}.asp&main={book_url_name.lower()}&file={book_seq_num}.{chapter}.htm"
    
    for attempt in range(max_retries):
        try:
            # Create request with proper headers
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
            
            with urllib.request.urlopen(req, timeout=10) as response:
                # Read raw bytes
                raw_data = response.read()
                
                # Try to decode as ISO-8859-7 (Greek encoding)
                try:
                    content = raw_data.decode('iso-8859-7')
                except:
                    # Fallback to UTF-8
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

def extract_chapter_text(html_content):
    """Extract all Greek text from a chapter page"""
    if not html_content:
        return []
        
    # Parse HTML
    parser = GreekBibleParser()
    parser.feed(html_content)
    
    verses = []
    if parser.text_parts:
        # The text is usually in one or more large blocks
        # We need to split it into verses
        full_text = ' '.join(parser.text_parts)
        
        # Look for verse numbers (digits followed by Greek text)
        # Pattern: number followed by Greek text
        verse_pattern = r'(\d+)\s+([^0-9]+?)(?=\d+\s+|$)'
        matches = re.findall(verse_pattern, full_text)
        
        for verse_num, verse_text in matches:
            # Clean the text
            verse_text = re.sub(r'\s+', ' ', verse_text).strip()
            if verse_text:
                verses.append((int(verse_num), verse_text))
    
    return verses

def fetch_book(book_folder_name, max_chapters=50):
    """Fetch a single book using the correct URL pattern"""
    # Load book mapping
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    if book_folder_name not in mapping:
        print(f"Unknown book: {book_folder_name}")
        return False
    
    book_info = mapping[book_folder_name]
    url_name = book_info['url_name']
    greek_name = book_info['greek_name']
    
    # Get sequence number
    seq_numbers = get_book_sequence_numbers()
    if book_folder_name not in seq_numbers:
        print(f"No sequence number for {book_folder_name}")
        return False
    
    book_seq = seq_numbers[book_folder_name]
    
    print(f"\nFetching {greek_name} (#{book_seq})")
    print(f"Folder: {book_folder_name}")
    print(f"URL name: {url_name}")
    print("=" * 50)
    
    book_dir = os.path.join(base_dir, book_folder_name)
    os.makedirs(book_dir, exist_ok=True)
    
    chapters_found = 0
    consecutive_failures = 0
    
    for chapter in range(1, max_chapters + 1):
        print(f"Chapter {chapter}: ", end='', flush=True)
        
        # Fetch the chapter
        content = fetch_chapter_text(url_name, book_seq, chapter)
        
        if content:
            verses = extract_chapter_text(content)
            
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
        
        time.sleep(0.5)  # Be respectful to the server
    
    if chapters_found > 0:
        print(f"\n✓ Successfully fetched {chapters_found} chapters of {greek_name}")
        return True
    else:
        print(f"\n✗ Failed to fetch any chapters of {greek_name}")
        return False

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fetch-septuagint-correct-pattern.py <book_folder> [max_chapters]")
        print("\nExample: python fetch-septuagint-correct-pattern.py genesis 50")
        return
    
    book_folder = sys.argv[1]
    max_chapters = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    fetch_book(book_folder, max_chapters)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os
import sys
import time
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

class GreekTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.verses = []
        self.current_verse = None
        self.current_text = []
        self.in_verse_marker = False
        self.capture_text = False
        
    def handle_starttag(self, tag, attrs):
        # Look for blue font tags that typically mark verse numbers
        if tag == 'font':
            for attr, value in attrs:
                if attr == 'color' and value == '#0000ff':
                    self.in_verse_marker = True
                    
    def handle_endtag(self, tag):
        if tag == 'font' and self.in_verse_marker:
            self.in_verse_marker = False
            self.capture_text = True
            
    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
            
        # Capture verse number
        if self.in_verse_marker and text.isdigit():
            # Save previous verse if exists
            if self.current_verse and self.current_text:
                verse_text = ' '.join(self.current_text).strip()
                # Clean up the text
                verse_text = re.sub(r'\s+', ' ', verse_text)
                if verse_text and any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in verse_text):
                    self.verses.append((self.current_verse, verse_text))
            
            self.current_verse = int(text)
            self.current_text = []
            
        # Capture Greek text after verse number
        elif self.capture_text and self.current_verse:
            # Check if it contains Greek characters
            if any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in text):
                self.current_text.append(text)
                
    def get_verses(self):
        # Don't forget the last verse
        if self.current_verse and self.current_text:
            verse_text = ' '.join(self.current_text).strip()
            verse_text = re.sub(r'\s+', ' ', verse_text)
            if verse_text:
                self.verses.append((self.current_verse, verse_text))
        return self.verses

def fetch_chapter(book_name, book_seq, chapter):
    """Fetch a single chapter"""
    main_param = book_name.lower()
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={main_param}&file={book_seq}.{chapter}.htm"
    
    try:
        req = Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept', 'text/html,application/xhtml+xml')
        req.add_header('Accept-Language', 'en-US,en;q=0.9')
        
        with urlopen(req, timeout=30) as response:
            content = response.read()
            # Try Greek encoding first
            try:
                html = content.decode('iso-8859-7')
            except:
                html = content.decode('utf-8', errors='ignore')
            
            # Extract verses
            parser = GreekTextExtractor()
            parser.feed(html)
            return parser.get_verses()
            
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def fetch_book(book_name, book_seq, total_chapters):
    """Fetch a complete book"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'apostoliki_diakonia', book_name)
    
    print(f"Fetching {book_name} ({total_chapters} chapters)")
    print("=" * 60)
    
    successful_chapters = 0
    
    for chapter in range(1, total_chapters + 1):
        print(f"Chapter {chapter}/{total_chapters}: ", end='', flush=True)
        
        verses = fetch_chapter(book_name, book_seq, chapter)
        
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
            successful_chapters += 1
        else:
            print("✗")
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\nCompleted: {successful_chapters}/{total_chapters} chapters")
    return successful_chapters > 0

# Book information
BOOKS = {
    'Exodos': {'seq': 2, 'chapters': 40},
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
    'Danihl': {'seq': 49, 'chapters': 12},
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        book_name = sys.argv[1]
        if book_name in BOOKS:
            info = BOOKS[book_name]
            fetch_book(book_name, info['seq'], info['chapters'])
        else:
            print(f"Unknown book: {book_name}")
            print(f"Available books: {', '.join(BOOKS.keys())}")
    else:
        # Default: fetch Exodos first
        print("Starting with Exodos...")
        info = BOOKS['Exodos']
        fetch_book('Exodos', info['seq'], info['chapters'])
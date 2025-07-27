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
    
    # Special cases for main parameter
    if book_name.startswith('Vasilion'):
        main_param = 'vasilion' + book_name[-1].lower()
    elif book_name.startswith('Paralipomenon'):
        main_param = 'paralipomenon' + book_name[-1].lower()
    elif book_name.startswith('Esdras'):
        main_param = 'esdras' + book_name[-1].lower()
    elif book_name.startswith('Makkavaion'):
        main_param = 'makkavaion' + book_name[-1].lower()
    
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

def fetch_missing_chapters():
    """Fetch all missing chapters from incomplete books"""
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia')
    
    # Missing chapters info
    missing_info = [
        ('Iov', 25, [25]),           # Missing chapter 25
        ('Parimiai', 26, [30, 31]),  # Missing chapters 30-31  
        ('Tovit', 18, [9]),          # Missing chapter 9
    ]
    
    for book_name, book_seq, missing_chapters in missing_info:
        print(f"\nFetching missing chapters for {book_name}")
        print("=" * 60)
        
        book_dir = os.path.join(base_dir, book_name)
        
        for chapter in missing_chapters:
            print(f"Chapter {chapter}: ", end='', flush=True)
            
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
            else:
                print("✗")
            
            # Rate limiting
            time.sleep(2)

if __name__ == "__main__":
    fetch_missing_chapters()
#!/usr/bin/env python3
import os
import sys
import time
import re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser

class VerseExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_td = False
        self.current_td = []
        self.verse_td = None
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
            self.current_td = []
            
    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False
            if self.current_td:
                content = ''.join(self.current_td)
                # Check if this TD has substantial Greek content
                greek_chars = len(re.findall(r'[\u0370-\u03ff\u1f00-\u1fff]', content))
                if greek_chars > 20 and not self.verse_td:
                    self.verse_td = content
            
    def handle_data(self, data):
        if self.in_td:
            self.current_td.append(data)

def parse_verses(text):
    """Parse the verse text into individual verses"""
    verses = []
    
    # Clean up the text
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Find verse patterns - numbers followed by Greek text
    # Verses are marked by numbers at the start or after some text
    parts = re.split(r'(\d+)', text)
    
    current_verse = None
    current_text = []
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
            
        if part.isdigit() and i > 0:  # This is a verse number
            # Save previous verse if exists
            if current_verse and current_text:
                verse_text = ' '.join(current_text).strip()
                if verse_text and any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in verse_text):
                    verses.append((current_verse, verse_text))
            
            current_verse = int(part)
            current_text = []
        elif current_verse is not None:
            # This is verse content
            if any('\u0370' <= c <= '\u03ff' or '\u1f00' <= c <= '\u1fff' for c in part):
                current_text.append(part)
    
    # Don't forget the last verse
    if current_verse and current_text:
        verse_text = ' '.join(current_text).strip()
        if verse_text:
            verses.append((current_verse, verse_text))
    
    return verses

def fetch_iov_chapter_25():
    """Fetch missing chapter 25 of Iov"""
    book_name = 'Iov'
    book_seq = 25
    chapter = 25
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia', book_name)
    
    print(f"\nFetching {book_name} chapter {chapter}")
    print("=" * 60)
    
    main_param = book_name.lower()
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={main_param}&file={book_seq}.{chapter}.htm"
    
    print(f"URL: {url}")
    
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
            
            # Extract verses using parser
            parser = VerseExtractor()
            parser.feed(html)
            
            if parser.verse_td:
                verses = parse_verses(parser.verse_td)
                
                if verses:
                    # Create chapter directory
                    chapter_dir = os.path.join(base_dir, str(chapter))
                    os.makedirs(chapter_dir, exist_ok=True)
                    
                    # Save each verse
                    for verse_num, verse_text in verses:
                        verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                        with open(verse_file, 'w', encoding='utf-8') as f:
                            f.write(verse_text)
                    
                    print(f"✓ Successfully fetched {len(verses)} verses")
                    return True
                else:
                    print("✗ No verses found")
            else:
                print("✗ No verse content found in HTML")
            
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
    except URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    fetch_iov_chapter_25()
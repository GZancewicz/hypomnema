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
                if greek_chars > 200 and not self.verse_td:
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
            
            # Extract verses using parser
            parser = VerseExtractor()
            parser.feed(html)
            
            if parser.verse_td:
                return parse_verses(parser.verse_td)
            
            return None
            
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except URLError as e:
        print(f"URL Error: {e.reason}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def find_last_chapter():
    """Find the last successfully fetched chapter"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia', 'Psalmoi')
    
    chapters = []
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            if item.isdigit():
                chapters.append(int(item))
    
    return max(chapters) if chapters else 0

def resume_psalmoi():
    """Resume fetching Psalmoi from where it left off"""
    book_name = 'Psalmoi'
    book_seq = 24
    total_chapters = 151
    
    # Find where we left off
    last_chapter = find_last_chapter()
    start_chapter = last_chapter + 1
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia', book_name)
    
    print(f"\nResuming {book_name} from chapter {start_chapter} (last fetched: {last_chapter}, total: {total_chapters} chapters)")
    print("=" * 60)
    
    successful_chapters = 0
    
    for chapter in range(start_chapter, total_chapters + 1):
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
    
    print(f"\nCompleted: {successful_chapters}/{total_chapters - start_chapter + 1} chapters")
    return successful_chapters > 0

if __name__ == "__main__":
    resume_psalmoi()
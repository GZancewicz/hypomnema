import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json

class VasilionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main_content = False
        self.text_parts = []
        self.current_text = []
        
    def handle_starttag(self, tag, attrs):
        # Look for the main content area
        if tag == 'td':
            for attr, value in attrs:
                if attr == 'width' and value == '560':
                    self.in_main_content = True
                    
    def handle_endtag(self, tag):
        if tag == 'td' and self.in_main_content:
            self.in_main_content = False
            
    def handle_data(self, data):
        if self.in_main_content:
            text = data.strip()
            # Skip navigation elements
            if text and not any(skip in text for skip in ['Πίσω', 'Κεφάλαιο', 'href=']):
                # Check if it contains Greek biblical text
                if len(text) > 10 and any('\u0370' <= char <= '\u03ff' or '\u1f00' <= char <= '\u1fff' for char in text):
                    self.text_parts.append(text)

def fetch_vasilion_chapter(book_url_name, book_seq_num, chapter, main_param):
    """Fetch a chapter from the Vasilion books"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_url_name}.asp&main={main_param}&file={book_seq_num}.{chapter}.htm"
    
    print(f"  Fetching URL: {url}")
    
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
        print(f"    Error: {e}")
        return None

def parse_vasilion_content(html_content):
    """Parse the Vasilion chapter content"""
    if not html_content:
        return []
    
    parser = VasilionParser()
    parser.feed(html_content)
    
    verses = []
    if parser.text_parts:
        # The text is usually in one big block
        full_text = ' '.join(parser.text_parts)
        
        # Clean up the text
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Try to identify verse numbers - they might be embedded in the text
        # Pattern 1: Simple numbers at the beginning
        parts = re.split(r'(\d+)\s*(?=\D)', full_text)
        
        current_verse = 0
        for i in range(0, len(parts)):
            if parts[i].isdigit():
                verse_num = int(parts[i])
                if i + 1 < len(parts):
                    verse_text = parts[i + 1].strip()
                    # Clean the verse text
                    verse_text = re.sub(r'^\W+', '', verse_text)  # Remove leading non-word chars
                    if verse_text and len(verse_text) > 5:
                        verses.append((verse_num, verse_text))
        
        # If no verses found with numbers, save the whole text as verse 1
        if not verses and full_text:
            print(f"    No verse numbers found, saving as single block")
            verses.append((1, full_text))
    
    return verses

def fetch_vasilion_book(book_folder, max_chapters=31):
    """Fetch one of the Vasilion books"""
    
    # Book configurations
    book_configs = {
        'vasiliona': {
            'url_name': 'VasilionA',
            'main_param': 'vasilionA',
            'seq_num': 9,
            'greek_name': 'ΒΑΣΙΛΕΙΩΝ Α\'',
            'chapters': 31
        },
        'vasilionb': {
            'url_name': 'VasilionB',
            'main_param': 'vasilionB',
            'seq_num': 10,
            'greek_name': 'ΒΑΣΙΛΕΙΩΝ Β\'',
            'chapters': 24
        },
        'vasiliong': {
            'url_name': 'VasilionG',
            'main_param': 'vasilionG',
            'seq_num': 11,
            'greek_name': 'ΒΑΣΙΛΕΙΩΝ Γ\'',
            'chapters': 22
        },
        'vasiliond': {
            'url_name': 'VasilionD',
            'main_param': 'vasilionD',
            'seq_num': 12,
            'greek_name': 'ΒΑΣΙΛΕΙΩΝ Δ\'',
            'chapters': 25
        }
    }
    
    if book_folder not in book_configs:
        print(f"Unknown book: {book_folder}")
        return False
    
    config = book_configs[book_folder]
    max_chapters = min(max_chapters, config['chapters'])
    
    print(f"\nFetching {config['greek_name']} ({book_folder})")
    print(f"Sequence: {config['seq_num']}")
    print(f"Chapters: {max_chapters}")
    print("=" * 60)
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint', book_folder)
    os.makedirs(base_dir, exist_ok=True)
    
    chapters_found = 0
    
    for chapter in range(1, max_chapters + 1):
        print(f"\nChapter {chapter}:")
        
        # Fetch the chapter
        content = fetch_vasilion_chapter(config['url_name'], config['seq_num'], 
                                        chapter, config['main_param'])
        
        if content:
            verses = parse_vasilion_content(content)
            
            if verses:
                # Create chapter directory
                chapter_dir = os.path.join(base_dir, str(chapter))
                os.makedirs(chapter_dir, exist_ok=True)
                
                # Save verses
                for verse_num, verse_text in verses:
                    verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                    with open(verse_file, 'w', encoding='utf-8') as f:
                        f.write(verse_text)
                
                print(f"  ✓ Saved {len(verses)} verses")
                chapters_found += 1
            else:
                print(f"  ✗ No verses found")
        else:
            print(f"  ✗ Failed to fetch")
            
        time.sleep(0.5)
    
    if chapters_found > 0:
        print(f"\n✓ Successfully fetched {chapters_found} chapters")
        return True
    else:
        print(f"\n✗ Failed to fetch any chapters")
        return False

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python fetch-vasilion-books.py <book_folder>")
        print("\nAvailable books:")
        print("  vasiliona - 1 Samuel (31 chapters)")
        print("  vasilionb - 2 Samuel (24 chapters)")
        print("  vasiliong - 1 Kings (22 chapters)")  
        print("  vasiliond - 2 Kings (25 chapters)")
        return
    
    book_folder = sys.argv[1]
    fetch_vasilion_book(book_folder)

if __name__ == "__main__":
    main()
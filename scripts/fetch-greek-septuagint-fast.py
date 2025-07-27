import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import codecs

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

def fetch_verse_with_encoding(book_name, chapter, verse, max_retries=2):
    """Fetch a verse handling ISO-8859-7 encoding"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={book_name.lower()}&file={chapter}.{verse}.htm"
    
    for attempt in range(max_retries):
        try:
            # Create request with proper headers
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
            
            with urllib.request.urlopen(req, timeout=5) as response:
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
                time.sleep(1)
                continue
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return None
    
    return None

def extract_greek_text(html_content):
    """Extract Greek text from HTML content"""
    if not html_content:
        return None
        
    # Parse HTML
    parser = GreekBibleParser()
    parser.feed(html_content)
    
    if parser.text_parts:
        # Join all parts and clean
        full_text = ' '.join(parser.text_parts)
        
        # Remove extra whitespace
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # Remove any remaining HTML tags
        full_text = re.sub(r'<[^>]+>', '', full_text)
        
        # Remove verse numbers at the beginning
        full_text = re.sub(r'^\d+\s*', '', full_text)
        
        return full_text.strip()
    
    return None

def fetch_chapter_fast(book_name, chapter_num, max_verses=60):
    """Fetch a chapter quickly with minimal retries"""
    verses = []
    consecutive_failures = 0
    verse_num = 1
    
    print(f"  Chapter {chapter_num}: ", end='', flush=True)
    
    while verse_num <= max_verses and consecutive_failures < 3:
        content = fetch_verse_with_encoding(book_name, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
                print(".", end='', flush=True)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
        else:
            consecutive_failures += 1
            
            # If we haven't found any verses yet, the chapter might not exist
            if not verses and consecutive_failures >= 3:
                break
        
        verse_num += 1
        time.sleep(0.3)  # Faster but still respectful
    
    print(f" ({len(verses)} verses)")
    return verses

def main():
    print("Fetching Greek Septuagint (LXX) - Fast Mode")
    print("Source: https://apostoliki-diakonia.gr/")
    print("=" * 50)
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Just do Genesis as a proof of concept
    print("\nProcessing Genesis...")
    
    book_dir = os.path.join(base_dir, 'genesis')
    os.makedirs(book_dir, exist_ok=True)
    
    output_file = os.path.join(book_dir, 'genesis.txt')
    
    # Process chapters and save incrementally
    total_verses = 0
    
    # Open file in append mode
    with open(output_file, 'w', encoding='utf-8') as f:
        # Fetch first 5 chapters
        for chapter in range(1, 6):
            verses = fetch_chapter_fast('Genesis', chapter)
            if verses:
                for verse in verses:
                    f.write(verse + '\n')
                f.flush()  # Force write to disk
                total_verses += len(verses)
            else:
                if chapter == 1:
                    print("  Failed to fetch chapter 1, stopping.")
                    break
    
    if total_verses > 0:
        print(f"\n✓ Saved Genesis: {total_verses} verses")
        print(f"  File: {output_file}")
    else:
        print("\n✗ Failed to fetch Genesis")

if __name__ == "__main__":
    main()
import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json
import sys

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

def fetch_chapter(book_url_name, chapter_num, chapter_dir, max_verses=80):
    """Fetch a chapter and save each verse as a separate file"""
    verses_found = 0
    consecutive_failures = 0
    verse_num = 1
    
    print(f"  Chapter {chapter_num}: ", end='', flush=True)
    
    while verse_num <= max_verses and consecutive_failures < 3:
        content = fetch_verse_with_encoding(book_url_name, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                # Save verse to file
                verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                with open(verse_file, 'w', encoding='utf-8') as f:
                    f.write(greek_text)
                
                verses_found += 1
                print(".", end='', flush=True)
                consecutive_failures = 0
            else:
                consecutive_failures += 1
        else:
            consecutive_failures += 1
            
            # If we haven't found any verses yet, the chapter might not exist
            if verses_found == 0 and consecutive_failures >= 3:
                break
        
        verse_num += 1
        time.sleep(0.3)  # Be respectful to the server
    
    if verses_found > 0:
        print(f" ✓ ({verses_found} verses)")
        return True
    else:
        print(" ✗ (no verses found)")
        # Remove empty chapter directory
        if os.path.exists(chapter_dir) and not os.listdir(chapter_dir):
            os.rmdir(chapter_dir)
        return False

def load_book_mapping():
    """Load the book mapping from JSON file"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch-septuagint-single-book.py <folder_name> [max_chapters]")
        print("\nAvailable books:")
        
        mapping = load_book_mapping()
        for folder_name, info in sorted(mapping.items()):
            print(f"  {folder_name:<20} - {info['greek_name']}")
        
        return
    
    folder_name = sys.argv[1]
    max_chapters = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    # Load book mapping
    mapping = load_book_mapping()
    if folder_name not in mapping:
        print(f"Error: Unknown book folder '{folder_name}'")
        print("Use script without arguments to see available books")
        return
    
    book_info = mapping[folder_name]
    url_name = book_info['url_name']
    greek_name = book_info['greek_name']
    
    print(f"Fetching {greek_name} ({folder_name})")
    print(f"URL name: {url_name}")
    print(f"Max chapters to try: {max_chapters}")
    print("=" * 50)
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint', folder_name)
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Process chapters
    chapters_found = 0
    consecutive_chapter_failures = 0
    
    for chapter in range(1, max_chapters + 1):
        chapter_dir = os.path.join(base_dir, str(chapter))
        os.makedirs(chapter_dir, exist_ok=True)
        
        if fetch_chapter(url_name, chapter, chapter_dir):
            chapters_found += 1
            consecutive_chapter_failures = 0
        else:
            consecutive_chapter_failures += 1
            # Stop if we fail to get 3 consecutive chapters
            if consecutive_chapter_failures >= 3 and chapters_found > 0:
                print(f"\nStopping - no more chapters found")
                break
    
    if chapters_found > 0:
        print(f"\n✓ Successfully fetched {chapters_found} chapters of {greek_name}")
    else:
        print(f"\n✗ Failed to fetch any chapters of {greek_name}")

if __name__ == "__main__":
    main()
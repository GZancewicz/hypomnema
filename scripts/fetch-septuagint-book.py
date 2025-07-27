import os
import urllib.request
import time
import re
from html.parser import HTMLParser
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

def fetch_chapter(book_name, chapter_num, max_verses=80):
    """Fetch a chapter with progress indication"""
    verses = []
    consecutive_failures = 0
    verse_num = 1
    
    print(f"  Fetching chapter {chapter_num}: ", end='', flush=True)
    
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
        time.sleep(0.3)  # Be respectful to the server
    
    if verses:
        print(f" ✓ ({len(verses)} verses)")
    else:
        print(" ✗ (no verses found)")
    
    return verses

def fetch_book(book_url_name, book_folder_name, max_chapters):
    """Fetch a single book"""
    print(f"\nFetching {book_url_name} ({max_chapters} chapters)...")
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    book_dir = os.path.join(base_dir, book_folder_name)
    os.makedirs(book_dir, exist_ok=True)
    
    output_file = os.path.join(book_dir, f"{book_folder_name}.txt")
    
    # Check if file exists and has content
    existing_verses = []
    last_chapter = 0
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_verses = f.readlines()
            if existing_verses:
                # Find last chapter
                for line in reversed(existing_verses):
                    match = re.match(r'^(\d+):', line.strip())
                    if match:
                        last_chapter = int(match.group(1))
                        break
                print(f"  Resuming from chapter {last_chapter + 1} (found {len(existing_verses)} existing verses)")
    
    all_verses = [v.strip() for v in existing_verses]
    chapters_found = last_chapter
    
    # Process remaining chapters
    for chapter in range(last_chapter + 1, max_chapters + 1):
        verses = fetch_chapter(book_url_name, chapter)
        
        if verses:
            all_verses.extend(verses)
            chapters_found += 1
            
            # Save after each chapter
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses) + '\n')
        else:
            # If we can't get 3 consecutive chapters, assume rest don't exist
            if chapter > 1 and chapter < max_chapters - 2:
                print(f"  Stopping at chapter {chapter} (no more content found)")
                break
    
    if chapters_found > 0:
        print(f"\n✓ Completed {book_url_name}: {chapters_found} chapters, {len(all_verses)} verses")
        print(f"  Saved to: {output_file}")
        return True
    else:
        print(f"\n✗ Failed to fetch any chapters for {book_url_name}")
        return False

def main():
    if len(sys.argv) < 2:
        # Default to Genesis
        book_url = "Genesis"
        book_folder = "genesis" 
        max_chapters = 50
    else:
        # Parse command line arguments
        book_url = sys.argv[1]
        book_folder = sys.argv[2] if len(sys.argv) > 2 else book_url.lower()
        max_chapters = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    
    print("Greek Septuagint Book Fetcher")
    print("Source: https://apostoliki-diakonia.gr/")
    print("=" * 50)
    
    success = fetch_book(book_url, book_folder, max_chapters)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
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

def fetch_verse_with_encoding(book_name, chapter, verse, max_retries=3):
    """Fetch a verse handling ISO-8859-7 encoding"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={book_name.lower()}&file={chapter}.{verse}.htm"
    
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
                time.sleep(2 * (attempt + 1))  # Exponential backoff
                continue
            else:
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
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

def fetch_chapter_robust(book_name, chapter_num, max_verses=100):
    """Fetch a chapter with robust error handling"""
    verses = []
    consecutive_failures = 0
    verse_num = 1
    
    print(f"  Chapter {chapter_num}:")
    
    while verse_num <= max_verses and consecutive_failures < 5:
        print(f"    Verse {verse_num}...", end='', flush=True)
        
        content = fetch_verse_with_encoding(book_name, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
                print(" ✓")
                consecutive_failures = 0
            else:
                print(" ✗ (no Greek text)")
                consecutive_failures += 1
        else:
            print(" ✗ (fetch failed)")
            consecutive_failures += 1
            
            # If we haven't found any verses yet, the chapter might not exist
            if not verses and consecutive_failures >= 3:
                break
        
        verse_num += 1
        time.sleep(1)  # Be respectful to the server
    
    return verses

def get_septuagint_books():
    """Return list of Septuagint books with their Greek URL names and estimated chapters"""
    return [
        # Pentateuch
        ('Genesis', 50),
        ('Exodus', 40),
        ('Levitikon', 27),
        ('Arithmoi', 36),
        ('Defteronomion', 34),
        # Historical
        ('Navi', 24),  # Joshua  
        ('Kritai', 21),  # Judges
        ('Routh', 4),  # Ruth
        ('Vasilion_A', 31),  # 1 Kings/Samuel
        ('Vasilion_B', 24),  # 2 Kings/Samuel
        ('Vasilion_G', 22),  # 3 Kings
        ('Vasilion_D', 25),  # 4 Kings
        ('Paralipomenon_A', 29),  # 1 Chronicles
        ('Paralipomenon_B', 36),  # 2 Chronicles
        ('Esdras_A', 10),
        ('Esdras_B', 10),  
        ('Neemias', 13),
        ('Tovit', 14),
        ('Ioudith', 16),
        ('Esthir', 16),
        ('Makkavaion_A', 16),
        ('Makkavaion_B', 15),
        ('Makkavaion_G', 7),
        # Wisdom
        ('Psalmoi', 151),
        ('Iov', 42),
        ('Parimiai', 31),  # Proverbs
        ('Ekklhsiastis', 12),
        ('Asma_Asmaton', 8),  # Song of Songs
        ('Sofia_Solomontos', 19),  # Wisdom
        ('Sofia_Sirach', 51),  # Sirach
        # Major Prophets
        ('Isaias', 66),
        ('Ieremias', 52),
        ('Thrinoi', 5),  # Lamentations
        ('Iechezikl', 48),
        ('Danil', 14),
        # Minor Prophets
        ('Osi', 14),  # Hosea
        ('Amos', 9),
        ('Michaias', 7),
        ('Iol', 4),  # Joel
        ('Avdiou', 1),  # Obadiah
        ('Ionas', 4),
        ('Naoum', 3),
        ('Avvakoum', 3),
        ('Sofonias', 3),
        ('Aggaios', 2),
        ('Zacharias', 14),
        ('Malachias', 4)
    ]

def main():
    print("Fetching Greek Septuagint (LXX) from Apostoliki Diakonia...")
    print("Source: https://apostoliki-diakonia.gr/")
    print("Note: Using ISO-8859-7 encoding conversion\n")
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    # Clean and recreate directory
    if os.path.exists(base_dir):
        import shutil
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    
    books = get_septuagint_books()
    successful_books = 0
    
    # Start with just Genesis and a few others to test
    test_books = [
        ('Genesis', 50),
        ('Exodus', 40),
        ('Psalmoi', 151)
    ]
    
    for book_name, max_chapters in test_books:
        print(f"\nProcessing {book_name}...")
        
        book_dir = os.path.join(base_dir, book_name.lower())
        os.makedirs(book_dir, exist_ok=True)
        
        all_verses = []
        
        # Try first 3 chapters
        for chapter in range(1, min(4, max_chapters + 1)):
            verses = fetch_chapter_robust(book_name, chapter)
            if verses:
                all_verses.extend(verses)
            else:
                # If we can't get any chapter, book might not be available
                if chapter == 1:
                    break
        
        if all_verses:
            output_file = os.path.join(book_dir, f"{book_name.lower()}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses) + '\n')
            
            print(f"  ✓ Saved {book_name}: {len(all_verses)} verses")
            successful_books += 1
        else:
            print(f"  ✗ No verses found for {book_name}")
            # Remove empty directory
            os.rmdir(book_dir)
    
    print(f"\n{'='*50}")
    print(f"Completed: {successful_books}/{len(test_books)} test books")
    print("Note: This is a test run. Full fetch would take many hours.")
    print("Greek text saved in Unicode UTF-8 format.")

if __name__ == "__main__":
    main()
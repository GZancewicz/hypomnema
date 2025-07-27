import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json
from datetime import datetime

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
    
    while verse_num <= max_verses and consecutive_failures < 3:
        content = fetch_verse_with_encoding(book_name, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
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
    
    return verses

def get_septuagint_books():
    """Return list of Septuagint books with their Greek URL names and estimated chapters"""
    return [
        # Pentateuch
        ('Genesis', 'genesis', 50),
        ('Exodus', 'exodus', 40),
        ('Levitikon', 'levitikon', 27),  # Leviticus
        ('Arithmoi', 'arithmoi', 36),  # Numbers
        ('Defteronomion', 'defteronomion', 34),  # Deuteronomy
        
        # Historical Books
        ('Navi', 'navi', 24),  # Joshua
        ('Kritai', 'kritai', 21),  # Judges
        ('Routh', 'routh', 4),  # Ruth
        ('Vasilion_A', 'vasilion_a', 31),  # 1 Samuel/Kings
        ('Vasilion_B', 'vasilion_b', 24),  # 2 Samuel/Kings
        ('Vasilion_G', 'vasilion_g', 22),  # 1 Kings (3rd)
        ('Vasilion_D', 'vasilion_d', 25),  # 2 Kings (4th)
        ('Paralipomenon_A', 'paralipomenon_a', 29),  # 1 Chronicles
        ('Paralipomenon_B', 'paralipomenon_b', 36),  # 2 Chronicles
        ('Esdras_A', 'esdras_a', 10),  # Ezra 1
        ('Esdras_B', 'esdras_b', 10),  # Ezra 2
        ('Neemias', 'neemias', 13),  # Nehemiah
        ('Tovit', 'tovit', 14),  # Tobit
        ('Ioudith', 'ioudith', 16),  # Judith
        ('Esthir', 'esthir', 16),  # Esther
        ('Makkavaion_A', 'makkavaion_a', 16),  # 1 Maccabees
        ('Makkavaion_B', 'makkavaion_b', 15),  # 2 Maccabees
        ('Makkavaion_G', 'makkavaion_g', 7),  # 3 Maccabees
        
        # Wisdom Books
        ('Psalmoi', 'psalmoi', 151),  # Psalms
        ('Iov', 'iov', 42),  # Job
        ('Parimiai', 'parimiai', 31),  # Proverbs
        ('Ekklhsiastis', 'ekklhsiastis', 12),  # Ecclesiastes
        ('Asma_Asmaton', 'asma_asmaton', 8),  # Song of Songs
        ('Sofia_Solomontos', 'sofia_solomontos', 19),  # Wisdom of Solomon
        ('Sofia_Sirach', 'sofia_sirach', 51),  # Sirach/Ecclesiasticus
        
        # Major Prophets
        ('Isaias', 'isaias', 66),  # Isaiah
        ('Ieremias', 'ieremias', 52),  # Jeremiah
        ('Thrinoi', 'thrinoi', 5),  # Lamentations
        ('Iechezikl', 'iechezikl', 48),  # Ezekiel
        ('Danil', 'danil', 14),  # Daniel (includes additions)
        
        # Minor Prophets
        ('Osi', 'osi', 14),  # Hosea
        ('Amos', 'amos', 9),
        ('Michaias', 'michaias', 7),  # Micah
        ('Iol', 'iol', 4),  # Joel
        ('Avdiou', 'avdiou', 1),  # Obadiah
        ('Ionas', 'ionas', 4),  # Jonah
        ('Naoum', 'naoum', 3),  # Nahum
        ('Avvakoum', 'avvakoum', 3),  # Habakkuk
        ('Sofonias', 'sofonias', 3),  # Zephaniah
        ('Aggaios', 'aggaios', 2),  # Haggai
        ('Zacharias', 'zacharias', 14),  # Zechariah
        ('Malachias', 'malachias', 4)  # Malachi
    ]

def save_progress(progress_file, book_name, status):
    """Save progress to file"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}
    
    progress[book_name] = {
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def load_progress(progress_file):
    """Load progress from file"""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

def main():
    print("Fetching Complete Greek Septuagint (LXX)")
    print("Source: https://apostoliki-diakonia.gr/")
    print("=" * 60)
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    os.makedirs(base_dir, exist_ok=True)
    
    # Progress tracking
    progress_file = os.path.join(base_dir, '_progress.json')
    progress = load_progress(progress_file)
    
    books = get_septuagint_books()
    total_books = len(books)
    successful_books = 0
    failed_books = []
    
    print(f"\nProcessing {total_books} books...")
    print(f"Progress will be saved to: {progress_file}\n")
    
    for i, (book_url, book_folder, max_chapters) in enumerate(books, 1):
        # Skip if already completed
        if book_folder in progress and progress[book_folder].get('status') == 'completed':
            print(f"[{i}/{total_books}] {book_url} - Already completed, skipping...")
            successful_books += 1
            continue
        
        print(f"\n[{i}/{total_books}] Processing {book_url} ({max_chapters} chapters)...")
        start_time = time.time()
        
        book_dir = os.path.join(base_dir, book_folder)
        os.makedirs(book_dir, exist_ok=True)
        
        output_file = os.path.join(book_dir, f"{book_folder}.txt")
        
        all_verses = []
        chapters_found = 0
        
        # Process all chapters
        for chapter in range(1, max_chapters + 1):
            print(f"  Chapter {chapter}/{max_chapters}: ", end='', flush=True)
            
            verses = fetch_chapter(book_url, chapter)
            
            if verses:
                all_verses.extend(verses)
                chapters_found += 1
                print(f"✓ ({len(verses)} verses)")
                
                # Save incrementally every 5 chapters
                if chapter % 5 == 0:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(all_verses) + '\n')
            else:
                print("✗ (no verses found)")
                # If first few chapters fail, book might not exist
                if chapter <= 3 and chapters_found == 0:
                    print(f"  Book {book_url} appears unavailable, stopping...")
                    break
        
        # Save final results
        if all_verses:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses) + '\n')
            
            elapsed = time.time() - start_time
            print(f"  ✓ Completed {book_url}: {chapters_found} chapters, {len(all_verses)} verses")
            print(f"  Time: {elapsed:.1f} seconds")
            print(f"  Saved to: {output_file}")
            
            successful_books += 1
            save_progress(progress_file, book_folder, 'completed')
        else:
            print(f"  ✗ Failed to fetch {book_url}")
            failed_books.append(book_url)
            save_progress(progress_file, book_folder, 'failed')
            # Remove empty directory
            if os.path.exists(book_dir) and not os.listdir(book_dir):
                os.rmdir(book_dir)
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  Total books: {total_books}")
    print(f"  Successful: {successful_books}")
    print(f"  Failed: {len(failed_books)}")
    
    if failed_books:
        print(f"\nFailed books:")
        for book in failed_books:
            print(f"  - {book}")
    
    print(f"\nGreek Septuagint text saved to: {base_dir}")
    print("All text in Unicode UTF-8 format")

if __name__ == "__main__":
    main()
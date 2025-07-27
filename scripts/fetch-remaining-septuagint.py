import os
import urllib.request
import time
import re
from html.parser import HTMLParser
import json

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

def get_book_sequence_numbers():
    """Return the sequence numbers for each book based on their order"""
    return {
        'Genesis': 1,
        'Exodos': 2,
        'Levitikon': 3,
        'Arithmoi': 4,
        'Defteronomion': 5,
        'Navi': 6,
        'Kritai': 7,
        'Routh': 8,
        'VasilionA': 9,
        'VasilionB': 10,
        'VasilionG': 11,
        'VasilionD': 12,
        'ParalipomenonA': 13,
        'ParalipomenonB': 14,
        'EsdrasA': 15,
        'EsdrasB': 16,
        'Neemias': 17,
        'Tovit': 18,
        'Ioudith': 19,
        'Esthir': 20,
        'MakkavaionA': 21,
        'MakkavaionB': 22,
        'makkavaionG': 23,  # lowercase G
        'Psalmoi': 24,
        'Iov': 25,
        'Parimiai': 26,
        'Ekklhsiastis': 27,
        'Asma_Asmaton': 28,
        'Sofia': 29,
        'Sofia_Sirah': 30,
        'Osie': 31,
        'Amos': 32,
        'Miheas': 33,
        'Iohl': 34,
        'Ovdiou': 35,
        'Ionas': 36,
        'Naoum': 37,
        'Amvakoum': 38,
        'Sofonias': 39,
        'Aggaios': 40,
        'Zaharias': 41,
        'Malahias': 42,
        'Hsaias': 43,
        'Ieremias': 44,
        'Varouh': 45,
        'Thrinoi': 46,
        'Epistoli_Ier': 47,
        'Iezekihl': 48,
        'Danihl': 49,
        'makkavaionD': 50  # lowercase D
    }

def fetch_verse_with_encoding(url_name, book_seq, chapter, verse, max_retries=2):
    """Fetch a verse handling ISO-8859-7 encoding"""
    # For books like VasilionA, need to handle main parameter differently
    main_param = url_name.lower()
    if url_name in ['VasilionA', 'VasilionB', 'VasilionG', 'VasilionD']:
        main_param = 'vasilion' + url_name[-1]
    elif url_name in ['ParalipomenonA', 'ParalipomenonB']:
        main_param = 'paralipomenon' + url_name[-1]
    elif url_name in ['EsdrasA', 'EsdrasB']:
        main_param = 'esdras' + url_name[-1]
    elif url_name in ['MakkavaionA', 'MakkavaionB']:
        main_param = 'makkavaion' + url_name[-1]
    
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{url_name}.asp&main={main_param}&file={book_seq}.{chapter}.{verse}.htm"
    
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_data = response.read()
                
                try:
                    content = raw_data.decode('iso-8859-7')
                except:
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
        
    parser = GreekBibleParser()
    parser.feed(html_content)
    
    if parser.text_parts:
        full_text = ' '.join(parser.text_parts)
        full_text = re.sub(r'\s+', ' ', full_text)
        full_text = re.sub(r'<[^>]+>', '', full_text)
        full_text = re.sub(r'^\d+\s*', '', full_text)
        
        return full_text.strip()
    
    return None

def fetch_chapter(folder_name, url_name, book_seq, chapter_num, max_verses=80):
    """Fetch a chapter with progress indication"""
    verses = []
    consecutive_failures = 0
    verse_num = 1
    
    while verse_num <= max_verses and consecutive_failures < 3:
        content = fetch_verse_with_encoding(url_name, book_seq, chapter_num, verse_num)
        
        if content:
            greek_text = extract_greek_text(content)
            
            if greek_text and len(greek_text) > 10:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
                consecutive_failures = 0
            else:
                consecutive_failures += 1
        else:
            consecutive_failures += 1
            
            if not verses and consecutive_failures >= 3:
                break
        
        verse_num += 1
        time.sleep(0.3)
    
    return verses

def fetch_remaining_books():
    """Fetch the remaining 12 books"""
    remaining_books = [
        ('VasilionA', 'Βασιλειών Α\'', 31),  # 1 Samuel
        ('VasilionB', 'Βασιλειών Β\'', 24),  # 2 Samuel
        ('VasilionG', 'Βασιλειών Γ\'', 22),  # 1 Kings
        ('VasilionD', 'Βασιλειών Δ\'', 25),  # 2 Kings
        ('ParalipomenonA', 'Παραλειπομένων Α\'', 29),  # 1 Chronicles
        ('ParalipomenonB', 'Παραλειπομένων Β\'', 36),  # 2 Chronicles
        ('EsdrasA', 'Έσδρας Α\'', 10),  # Ezra 1
        ('EsdrasB', 'Έσδρας Β\'', 10),  # Ezra 2
        ('MakkavaionA', 'Μακκαβαίων Α\'', 16),  # 1 Maccabees
        ('MakkavaionB', 'Μακκαβαίων Β\'', 15),  # 2 Maccabees
        ('makkavaionG', 'Μακκαβαίων Γ\'', 7),   # 3 Maccabees
        ('makkavaionD', 'Μακκαβαίων Δ\'', 18),  # 4 Maccabees
    ]
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    seq_numbers = get_book_sequence_numbers()
    
    for folder_name, greek_name, max_chapters in remaining_books:
        print(f"\nProcessing {greek_name} ({folder_name})...")
        
        if folder_name not in seq_numbers:
            print(f"  No sequence number found for {folder_name}")
            continue
            
        book_seq = seq_numbers[folder_name]
        book_dir = os.path.join(base_dir, folder_name)
        os.makedirs(book_dir, exist_ok=True)
        
        chapters_found = 0
        
        for chapter in range(1, max_chapters + 1):
            print(f"  Chapter {chapter}/{max_chapters}: ", end='', flush=True)
            
            verses = fetch_chapter(folder_name, folder_name, book_seq, chapter)
            
            if verses:
                # Create chapter directory
                chapter_dir = os.path.join(book_dir, str(chapter))
                os.makedirs(chapter_dir, exist_ok=True)
                
                # Save each verse
                for verse_text in verses:
                    match = re.match(r'^(\d+):(\d+)\s+(.+)$', verse_text)
                    if match:
                        verse_num = match.group(2)
                        text = match.group(3)
                        verse_file = os.path.join(chapter_dir, f"{verse_num}.txt")
                        with open(verse_file, 'w', encoding='utf-8') as f:
                            f.write(text)
                
                print(f"✓ ({len(verses)} verses)")
                chapters_found += 1
            else:
                print("✗ (no verses found)")
                # If first few chapters fail, book might not exist
                if chapter <= 3 and chapters_found == 0:
                    print(f"  Book {folder_name} appears unavailable, stopping...")
                    break
        
        if chapters_found > 0:
            print(f"  ✓ Completed {folder_name}: {chapters_found} chapters")
        else:
            print(f"  ✗ Failed to fetch {folder_name}")

def main():
    print("Fetching Remaining Greek Septuagint Books")
    print("=" * 60)
    fetch_remaining_books()

if __name__ == "__main__":
    main()
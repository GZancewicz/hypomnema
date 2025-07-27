import os
import urllib.request
import time
import re
from html.parser import HTMLParser

class GreekTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_content = False
        self.current_text = []
        
    def handle_starttag(self, tag, attrs):
        # Look for content areas
        if tag in ['p', 'div', 'span']:
            for attr_name, attr_value in attrs:
                if attr_name == 'class' and 'content' in (attr_value or ''):
                    self.in_content = True
                    
    def handle_endtag(self, tag):
        if tag in ['p', 'div', 'span'] and self.in_content:
            self.in_content = False
            
    def handle_data(self, data):
        # Collect all text, we'll filter later
        text = data.strip()
        if text and len(text) > 5:  # Skip very short strings
            self.current_text.append(text)

def clean_greek_text(text):
    """Clean and extract Greek text"""
    # Remove HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    
    # Remove verse numbers at start if present
    text = re.sub(r'^\d+\s*', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def fetch_chapter(book_name, chapter_num, max_verses=100):
    """Fetch a complete chapter by getting all verses"""
    base_url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={book_name.lower()}&file="
    
    verses = []
    verse_num = 1
    consecutive_failures = 0
    
    while verse_num <= max_verses and consecutive_failures < 3:
        try:
            url = f"{base_url}{chapter_num}.{verse_num}.htm"
            print(f"    Fetching {chapter_num}:{verse_num}...", end='', flush=True)
            
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            # Parse the content
            parser = GreekTextParser()
            parser.feed(content)
            
            # Find Greek text (contains Greek characters)
            greek_text = None
            for text in parser.current_text:
                if re.search(r'[α-ωΑ-Ω]', text):  # Contains Greek characters
                    greek_text = clean_greek_text(text)
                    if len(greek_text) > 10:  # Reasonable length
                        break
            
            if greek_text:
                verses.append(f"{chapter_num}:{verse_num} {greek_text}")
                print(" ✓")
                verse_num += 1
                consecutive_failures = 0
            else:
                print(" ✗ (no text)")
                consecutive_failures += 1
                verse_num += 1
                
            time.sleep(0.5)  # Be respectful
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(" (end)")
                break
            else:
                print(f" ✗ ({e.code})")
                consecutive_failures += 1
                if e.code == 500:
                    verse_num += 1  # Try next verse
                else:
                    break
        except Exception as e:
            print(f" ✗ ({e})")
            consecutive_failures += 1
            verse_num += 1
    
    return verses

def get_septuagint_books():
    """Return list of Septuagint books with their Greek URL names"""
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
        # Prophets
        ('Isaias', 66),
        ('Ieremias', 52),
        ('Thrinoi', 5),  # Lamentations
        ('Iechezikl', 48),
        ('Danil', 14),
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
    print("Note: Using Greek folder names as found on the website\n")
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    os.makedirs(base_dir, exist_ok=True)
    
    books = get_septuagint_books()
    successful_books = 0
    
    # Test with just first 3 books
    for book_name, max_chapters in books[:3]:
        print(f"\nProcessing {book_name}...")
        
        book_dir = os.path.join(base_dir, book_name.lower())
        os.makedirs(book_dir, exist_ok=True)
        
        all_verses = []
        
        # Fetch first chapter to test
        verses = fetch_chapter(book_name, 1)
        if verses:
            all_verses.extend(verses)
            
            # If first chapter worked, try chapter 2
            if len(verses) > 10:
                verses2 = fetch_chapter(book_name, 2)
                if verses2:
                    all_verses.extend(verses2)
        
        if all_verses:
            # Save what we got
            output_file = os.path.join(book_dir, f"{book_name.lower()}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses) + '\n')
            
            print(f"  Saved {book_name}: {len(all_verses)} verses")
            successful_books += 1
        else:
            print(f"  ✗ No verses found for {book_name}")
    
    print(f"\nCompleted: {successful_books}/{len(books[:3])} books tested")
    print("Note: This is a test run with first 3 books only.")

if __name__ == "__main__":
    main()
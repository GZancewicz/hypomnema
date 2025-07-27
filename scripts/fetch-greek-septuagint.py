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

def fetch_chapter(book_name, chapter_num):
    """Fetch a complete chapter by getting all verses"""
    base_url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{book_name}.asp&main={book_name.lower()}&file="
    
    verses = []
    verse_num = 1
    
    while True:
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
            else:
                print(" ✗ (no text)")
                break
                
            time.sleep(0.5)  # Be respectful
            
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(" (end)")
                break
            else:
                print(f" ✗ ({e.code})")
                break
        except Exception as e:
            print(f" ✗ ({e})")
            break
    
    return verses

def get_septuagint_books():
    """Return list of Septuagint books with their Greek names"""
    return [
        ('Genesis', 'genesis', 50),
        ('Exodus', 'exodus', 40),
        ('Leviticus', 'leviticus', 27),
        ('Numbers', 'numbers', 36),
        ('Deuteronomy', 'deuteronomy', 34),
        ('Joshua', 'joshua', 24),
        ('Judges', 'judges', 21),
        ('Ruth', 'ruth', 4),
        ('1Kings', '1kings', 31),  # 1 Samuel
        ('2Kings', '2kings', 24),  # 2 Samuel
        ('3Kings', '3kings', 22),  # 1 Kings
        ('4Kings', '4kings', 25),  # 2 Kings
        ('1Chronicles', '1chronicles', 29),
        ('2Chronicles', '2chronicles', 36),
        ('Ezra', 'ezra', 10),
        ('Nehemiah', 'nehemiah', 13),
        ('Esther', 'esther', 16),
        ('Job', 'job', 42),
        ('Psalms', 'psalms', 151),
        ('Proverbs', 'proverbs', 31),
        ('Ecclesiastes', 'ecclesiastes', 12),
        ('SongOfSongs', 'songofSongs', 8),
        ('Isaiah', 'isaiah', 66),
        ('Jeremiah', 'jeremiah', 52),
        ('Lamentations', 'lamentations', 5),
        ('Ezekiel', 'ezekiel', 48),
        ('Daniel', 'daniel', 14),  # Including Greek additions
        ('Hosea', 'hosea', 14),
        ('Amos', 'amos', 9),
        ('Micah', 'micah', 7),
        ('Joel', 'joel', 4),
        ('Obadiah', 'obadiah', 1),
        ('Jonah', 'jonah', 4),
        ('Nahum', 'nahum', 3),
        ('Habakkuk', 'habakkuk', 3),
        ('Zephaniah', 'zephaniah', 3),
        ('Haggai', 'haggai', 2),
        ('Zechariah', 'zechariah', 14),
        ('Malachi', 'malachi', 3),
        ('Tobit', 'tobit', 14),
        ('Judith', 'judith', 16),
        ('Wisdom', 'wisdom', 19),
        ('Sirach', 'sirach', 51),
        ('Baruch', 'baruch', 6),
        ('1Maccabees', '1maccabees', 16),
        ('2Maccabees', '2maccabees', 15),
        ('3Maccabees', '3maccabees', 7),
        ('4Maccabees', '4maccabees', 18)
    ]

def main():
    print("Fetching Greek Septuagint (LXX) from Apostoliki Diakonia...")
    print("Source: https://apostoliki-diakonia.gr/")
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    os.makedirs(base_dir, exist_ok=True)
    
    books = get_septuagint_books()
    successful_books = 0
    
    for book_display, book_folder, max_chapters in books:
        print(f"\nProcessing {book_display}...")
        
        book_dir = os.path.join(base_dir, book_folder)
        os.makedirs(book_dir, exist_ok=True)
        
        all_verses = []
        
        # Try first few chapters to see if book exists
        for chapter in range(1, min(max_chapters + 1, 4)):  # Start with first 3 chapters
            verses = fetch_chapter(book_display, chapter)
            if verses:
                all_verses.extend(verses)
            else:
                break
        
        if all_verses:
            # Save what we got
            output_file = os.path.join(book_dir, f"{book_folder}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses) + '\n')
            
            print(f"  Saved {book_folder}: {len(all_verses)} verses")
            successful_books += 1
        else:
            print(f"  ✗ No verses found for {book_display}")
    
    print(f"\nCompleted: {successful_books}/{len(books)} books processed")
    print("Note: This is a partial fetch to test the pattern. Full fetch would take hours.")

if __name__ == "__main__":
    main()
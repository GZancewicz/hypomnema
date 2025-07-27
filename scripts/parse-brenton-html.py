import os
import re
from html.parser import HTMLParser

class BrentonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_verse = False
        self.current_verse = ""
        self.current_verse_num = ""
        self.verses = []
        self.in_chapter_label = False
        self.current_chapter = ""
        
    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            for attr_name, attr_value in attrs:
                if attr_name == 'class' and attr_value == 'verse':
                    self.in_verse = True
                    # Extract verse ID
                    for name, value in attrs:
                        if name == 'id' and value.startswith('V'):
                            self.current_verse_num = value[1:]  # Remove 'V' prefix
        elif tag == 'div':
            for attr_name, attr_value in attrs:
                if attr_name == 'class' and attr_value == 'chapterlabel':
                    self.in_chapter_label = True
                    
    def handle_endtag(self, tag):
        if tag == 'span' and self.in_verse:
            self.in_verse = False
        elif tag == 'div' and self.in_chapter_label:
            self.in_chapter_label = False
            
    def handle_data(self, data):
        if self.in_chapter_label:
            self.current_chapter = data.strip()
        elif self.in_verse:
            # The verse number is in the span
            pass
        elif self.current_verse_num and not self.in_verse:
            # This is the verse text after the verse span
            text = data.strip()
            if text and not text.isdigit():
                # Clean up the text
                text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
                text = re.sub(r'^\d+\s*', '', text)  # Remove leading numbers
                if self.current_chapter and text:
                    self.verses.append(f"{self.current_chapter}:{self.current_verse_num} {text}")
                    self.current_verse_num = ""

def parse_html_file(filepath):
    """Parse a single HTML file and return the verses"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove footnotes and references
    content = re.sub(r'<a[^>]*class="notemark"[^>]*>.*?</a>', '', content)
    content = re.sub(r'<span[^>]*class="popup"[^>]*>.*?</span>', '', content)
    
    parser = BrentonParser()
    parser.feed(content)
    
    return parser.verses

def get_book_mapping():
    """Map HTML filenames to book folder names"""
    return {
        # Old Testament
        'GEN': 'genesis',
        'EXO': 'exodus', 
        'LEV': 'leviticus',
        'NUM': 'numbers',
        'DEU': 'deuteronomy',
        'JOS': 'joshua',
        'JDG': 'judges',
        'RUT': 'ruth',
        '1SA': '1samuel',
        '2SA': '2samuel',
        '1KI': '1kings',
        '2KI': '2kings',
        '1CH': '1chronicles',
        '2CH': '2chronicles',
        'EZR': 'ezra',
        'NEH': 'nehemiah',
        'EST': 'esther',
        'JOB': 'job',
        'PSA': 'psalms',
        'PRO': 'proverbs',
        'ECC': 'ecclesiastes',
        'SOL': 'song_of_solomon',
        'ISA': 'isaiah',
        'JER': 'jeremiah',
        'LAM': 'lamentations',
        'EZE': 'ezekiel',
        'DAN': 'daniel',
        'HOS': 'hosea',
        'JOE': 'joel',
        'AMO': 'amos',
        'OBA': 'obadiah',
        'JON': 'jonah',
        'MIC': 'micah',
        'NAH': 'nahum',
        'HAB': 'habakkuk',
        'ZEP': 'zephaniah',
        'HAG': 'haggai',
        'ZEC': 'zechariah',
        'MAL': 'malachi',
        # Deuterocanonical books
        'TOB': 'tobit',
        'JDT': 'judith',
        'WIS': 'wisdom',
        'SIR': 'sirach',
        'BAR': 'baruch',
        'LJE': 'letter_of_jeremiah',
        'DAG': 'prayer_of_azariah',  # Daniel Greek additions
        'SUS': 'susanna',
        'BEL': 'bel_and_the_dragon',
        '1MA': '1maccabees',
        '2MA': '2maccabees',
        '3MA': '3maccabees',
        '4MA': '4maccabees',
        'MAN': 'prayer_of_manasseh',
        '1ES': '1esdras',
        '2ES': '2esdras'
    }

def main():
    book_mapping = get_book_mapping()
    base_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.dirname(base_path)
    
    # Process all HTML files
    for book_prefix, folder_name in book_mapping.items():
        print(f"Processing {folder_name}...")
        
        # Find all chapter files for this book
        chapter_files = []
        for filename in os.listdir(parent_path):
            if filename.startswith(book_prefix) and filename.endswith('.htm') and len(filename) > 7:
                # This is a chapter file (e.g., GEN01.htm)
                chapter_files.append(filename)
        
        if not chapter_files:
            print(f"  No files found for {book_prefix}")
            continue
            
        chapter_files.sort()
        
        # Combine all chapters
        all_verses = []
        for chapter_file in chapter_files:
            filepath = os.path.join(parent_path, chapter_file)
            if os.path.exists(filepath):
                verses = parse_html_file(filepath)
                all_verses.extend(verses)
                print(f"  Parsed {chapter_file}: {len(verses)} verses")
        
        if all_verses:
            # Save to text file
            output_path = os.path.join(parent_path, 'texts', 'english', 'brenton', folder_name, f'{folder_name}.txt')
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(all_verses))
            
            print(f"  Saved {folder_name}: {len(all_verses)} verses total")
        else:
            print(f"  No verses found for {folder_name}")

if __name__ == "__main__":
    main()
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

def get_missing_books():
    """Map HTML filenames to book folder names for missing books"""
    return {
        'ESG': ('esther', 'Esther (Greek)'),
        'SNG': ('song_of_solomon', 'Song of Solomon'),
        'EZK': ('ezekiel', 'Ezekiel'),
        'DAG': ('daniel', 'Daniel (including Greek portions)'),
        'JOL': ('joel', 'Joel'),
        'NAM': ('nahum', 'Nahum'),
        '2ES': ('2esdras', '2 Esdras')
    }

def main():
    missing_books = get_missing_books()
    base_path = os.path.dirname(os.path.abspath(__file__))
    parent_path = os.path.dirname(base_path)
    
    # Process missing books
    for book_prefix, (folder_name, book_title) in missing_books.items():
        print(f"Processing {book_title} ({folder_name})...")
        
        # Find all chapter files for this book
        chapter_files = []
        for filename in os.listdir(parent_path):
            if filename.startswith(book_prefix) and filename.endswith('.htm') and len(filename) > 7:
                # This is a chapter file (e.g., ESG01.htm)
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
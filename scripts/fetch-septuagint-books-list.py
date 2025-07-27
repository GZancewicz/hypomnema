import os
import urllib.request
import re
from html.parser import HTMLParser
import json

class BookListParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_link = False
        self.current_href = None
        self.books = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr, value in attrs:
                if attr == 'href' and 'contents_' in value and '.asp' in value:
                    self.in_link = True
                    self.current_href = value
                    
    def handle_endtag(self, tag):
        if tag == 'a':
            self.in_link = False
            
    def handle_data(self, data):
        if self.in_link and self.current_href:
            text = data.strip()
            if text and not text.startswith('<'):
                # Extract book name from URL
                match = re.search(r'contents_([^.]+)\.asp', self.current_href)
                if match:
                    url_name = match.group(1)
                    self.books.append({
                        'greek_name': text,
                        'url_name': url_name,
                        'folder_name': url_name.lower()
                    })

def fetch_books_list():
    """Fetch the list of books from the main OT page"""
    url = "https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents.asp&main=OldTes"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        req.add_header('Accept-Charset', 'ISO-8859-7,utf-8')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            raw_data = response.read()
            
            # Try to decode as ISO-8859-7 (Greek encoding)
            try:
                content = raw_data.decode('iso-8859-7')
            except:
                content = raw_data.decode('utf-8', errors='ignore')
            
            return content
    except Exception as e:
        print(f"Error fetching books list: {e}")
        return None

def main():
    print("Fetching Greek Septuagint Book List")
    print("Source: https://apostoliki-diakonia.gr/")
    print("=" * 50)
    
    # Fetch the main page
    content = fetch_books_list()
    if not content:
        print("Failed to fetch books list")
        return
    
    # Parse the books
    parser = BookListParser()
    parser.feed(content)
    
    if not parser.books:
        print("No books found in the page")
        return
    
    print(f"\nFound {len(parser.books)} books:")
    
    # Create base directory
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    os.makedirs(base_dir, exist_ok=True)
    
    # Create directories and save mapping
    book_mapping = {}
    
    for book in parser.books:
        print(f"  {book['greek_name']} -> {book['folder_name']}")
        
        # Create directory
        book_dir = os.path.join(base_dir, book['folder_name'])
        os.makedirs(book_dir, exist_ok=True)
        
        # Add to mapping
        book_mapping[book['folder_name']] = {
            'greek_name': book['greek_name'],
            'url_name': book['url_name'],
            'english_name': ''  # To be filled in later
        }
    
    # Save the mapping
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(book_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\nCreated {len(parser.books)} directories")
    print(f"Book mapping saved to: {mapping_file}")

if __name__ == "__main__":
    main()
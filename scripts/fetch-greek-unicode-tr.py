import os
import urllib.request
import re

# Book code to folder name mapping
book_mapping = {
    '40': 'matthew',
    '41': 'mark',
    '42': 'luke', 
    '43': 'john',
    '44': 'acts',
    '45': 'romans',
    '46': '1corinthians',
    '47': '2corinthians',
    '48': 'galatians',
    '49': 'ephesians',
    '50': 'philippians',
    '51': 'colossians',
    '52': '1thessalonians',
    '53': '2thessalonians',
    '54': '1timothy',
    '55': '2timothy',
    '56': 'titus',
    '57': 'philemon',
    '58': 'hebrews',
    '59': 'james',
    '60': '1peter',
    '61': '2peter',
    '62': '1john',
    '63': '2john',
    '64': '3john',
    '65': 'jude',
    '66': 'revelation'
}

def download_kjtr():
    """Download the KJTR Greek text"""
    url = "https://raw.githubusercontent.com/Center-for-New-Testament-Restoration/KJTR/master/KJTR.txt"
    print("Downloading KJTR Greek text...")
    
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    
    return content

def parse_kjtr_line(line):
    """Parse a KJTR line into components"""
    # Format: 40001001 ¶Βίβλος γενέσεως...
    # First 2 digits = book, next 3 = chapter, last 3 = verse
    
    line = line.strip()
    if not line or len(line) < 8:
        return None
        
    try:
        reference = line[:8]
        text = line[8:].strip()
        
        # Remove paragraph markers
        text = text.replace('¶', '').strip()
        
        book_code = reference[:2]
        chapter = int(reference[2:5])
        verse = int(reference[5:8])
        
        if book_code in book_mapping:
            return {
                'book': book_mapping[book_code],
                'chapter': chapter,
                'verse': verse,
                'text': text
            }
    except:
        return None
    
    return None

def save_books(content):
    """Parse content and save to individual book files"""
    lines = content.strip().split('\n')
    
    # Group verses by book
    books = {}
    
    for line in lines:
        parsed = parse_kjtr_line(line)
        if parsed:
            book = parsed['book']
            if book not in books:
                books[book] = []
            
            verse_ref = f"{parsed['chapter']}:{parsed['verse']}"
            books[book].append((verse_ref, parsed['text']))
    
    # Save each book
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'textus_receptus')
    
    for book_name, verses in books.items():
        book_dir = os.path.join(base_dir, book_name)
        os.makedirs(book_dir, exist_ok=True)
        
        output_file = os.path.join(book_dir, f"{book_name}.txt")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for ref, text in verses:
                f.write(f"{ref} {text}\n")
        
        print(f"  Saved {book_name}: {len(verses)} verses")

def main():
    print("Fetching Textus Receptus Greek New Testament (Unicode)...")
    print("Source: King James Textus Receptus (KJTR) by Alan Bunning")
    print("License: CC BY 4.0\n")
    
    # Clean existing directory
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'textus_receptus')
    
    if os.path.exists(base_dir):
        import shutil
        shutil.rmtree(base_dir)
    
    os.makedirs(base_dir)
    
    # Download and parse
    content = download_kjtr()
    print(f"Downloaded {len(content)} characters\n")
    
    print("Parsing and saving books:")
    save_books(content)
    
    print(f"\nCompleted! All books saved to {base_dir}")
    print("\nNote: Per CC BY 4.0 license, attribution required:")
    print("Text: Alan Bunning, Center for New Testament Restoration (2014)")

if __name__ == "__main__":
    main()
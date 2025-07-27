import json
import os
import urllib.request
import time

single_chapter_books = [
    ("2john", "2John", 13),
    ("3john", "3John", 14),
    ("jude", "Jude", 25),
    ("philemon", "Philemon", 25)
]

def fetch_verse(book_abbr, verse_num):
    """Fetch a single verse"""
    url = f"https://bible-api.com/{book_abbr}+1:{verse_num}?translation=kjv"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            verses = data.get('verses', [])
            if verses:
                return verses[0].get('text', '').strip()
    except:
        return None
    
    return None

def main():
    base_path = os.path.join(os.path.dirname(__file__), '..', 'texts', 'english', 'kjv')
    
    for folder_name, book_abbr, total_verses in single_chapter_books:
        print(f"\nFixing {folder_name}...")
        
        book_text = ""
        
        for verse_num in range(1, total_verses + 1):
            print(f"  Verse {verse_num}/{total_verses}", end='', flush=True)
            
            verse_text = fetch_verse(book_abbr, verse_num)
            
            if verse_text:
                book_text += f"1:{verse_num} {verse_text}\n"
                print(" ✓")
            else:
                print(" ✗")
                # Continue trying other verses
            
            time.sleep(0.5)  # Rate limiting
        
        # Save the book
        if book_text:
            file_path = os.path.join(base_path, folder_name, f"{folder_name}.txt")
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(book_text)
            
            lines = book_text.strip().count('\n') + 1
            print(f"  Saved {folder_name} ({lines} verses)")
        else:
            print(f"  Failed to fetch {folder_name}")

if __name__ == "__main__":
    main()
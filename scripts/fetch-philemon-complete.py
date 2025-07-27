import json
import os
import urllib.request
import time

def fetch_verse(verse_num):
    """Fetch a single verse"""
    url = f"https://bible-api.com/Philemon+1:{verse_num}?translation=kjv"
    
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
    book_text = ""
    verse_num = 1
    
    # Philemon has 25 verses
    while verse_num <= 25:
        print(f"Fetching verse {verse_num}...", end='', flush=True)
        
        verse_text = fetch_verse(verse_num)
        
        if verse_text:
            book_text += f"1:{verse_num} {verse_text}\n"
            print(" ✓")
        else:
            print(" ✗")
            break
        
        verse_num += 1
        time.sleep(0.5)  # Rate limiting
    
    # Save the book
    if book_text:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'texts', 'english', 'kjv', 'philemon', 'philemon.txt')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(book_text)
        
        print(f"\nSaved Philemon ({verse_num - 1} verses)")
    else:
        print("\nFailed to fetch Philemon")

if __name__ == "__main__":
    main()
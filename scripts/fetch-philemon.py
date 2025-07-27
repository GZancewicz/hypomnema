import json
import os
import urllib.request

def main():
    url = "https://bible-api.com/Philemon+1?translation=kjv"
    
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
        verses = data.get('verses', [])
    
    book_text = ""
    for verse in verses:
        verse_num = verse.get('verse', 0)
        verse_text = verse.get('text', '').strip()
        
        if verse_num and verse_text:
            book_text += f"1:{verse_num} {verse_text}\n"
    
    # Save the book
    file_path = os.path.join(os.path.dirname(__file__), '..', 'texts', 'english', 'kjv', 'philemon', 'philemon.txt')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(book_text)
    
    print(f"Saved Philemon ({len(verses)} verses)")

if __name__ == "__main__":
    main()
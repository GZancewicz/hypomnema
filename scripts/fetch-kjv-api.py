import json
import os
import time
import urllib.request
import urllib.error

books = [
    ("matthew", "Matt", 28),
    ("mark", "Mark", 16),
    ("luke", "Luke", 24),
    ("john", "John", 21),
    ("acts", "Acts", 28),
    ("romans", "Rom", 16),
    ("1corinthians", "1Cor", 16),
    ("2corinthians", "2Cor", 13),
    ("galatians", "Gal", 6),
    ("ephesians", "Eph", 6),
    ("philippians", "Phil", 4),
    ("colossians", "Col", 4),
    ("1thessalonians", "1Thess", 5),
    ("2thessalonians", "2Thess", 3),
    ("1timothy", "1Tim", 6),
    ("2timothy", "2Tim", 4),
    ("titus", "Titus", 3),
    ("philemon", "Phlm", 1),
    ("hebrews", "Heb", 13),
    ("james", "Jas", 5),
    ("1peter", "1Pet", 5),
    ("2peter", "2Pet", 3),
    ("1john", "1John", 5),
    ("2john", "2John", 1),
    ("3john", "3John", 1),
    ("jude", "Jude", 1),
    ("revelation", "Rev", 22)
]

def fetch_chapter(book_abbr, chapter):
    """Fetch a single chapter from the API"""
    url = f"https://bible-api.com/{book_abbr}+{chapter}?translation=kjv"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            return data.get('text', '')
    except urllib.error.URLError as e:
        print(f"Error fetching {book_abbr} {chapter}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def main():
    base_path = os.path.join(os.path.dirname(__file__), '..', 'texts', 'english', 'kjv')
    
    for folder_name, book_abbr, num_chapters in books:
        print(f"Processing {folder_name}...")
        
        book_text = ""
        
        for chapter in range(1, num_chapters + 1):
            print(f"  Fetching chapter {chapter}/{num_chapters}")
            
            chapter_text = fetch_chapter(book_abbr, chapter)
            
            if chapter_text:
                # Clean up the text
                verses = chapter_text.strip().split('\n')
                for verse in verses:
                    if verse.strip():
                        # Add chapter:verse format
                        verse_parts = verse.strip().split(' ', 1)
                        if len(verse_parts) == 2 and verse_parts[0].isdigit():
                            verse_num = verse_parts[0]
                            verse_text = verse_parts[1]
                            book_text += f"{chapter}:{verse_num} {verse_text}\n"
                        else:
                            book_text += verse.strip() + '\n'
            
            # Be respectful to the API
            time.sleep(0.5)
        
        # Save the book
        file_path = os.path.join(base_path, folder_name, f"{folder_name}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(book_text)
        
        print(f"Saved {folder_name}")

if __name__ == "__main__":
    main()
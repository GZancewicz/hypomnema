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
            return data.get('verses', [])
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
        book_path = os.path.join(base_path, folder_name)
        
        # Create a full book text file
        full_book_text = ""
        
        for chapter_num in range(1, num_chapters + 1):
            print(f"  Fetching chapter {chapter_num}/{num_chapters}")
            
            # Create chapter folder
            chapter_path = os.path.join(book_path, f"chapter-{chapter_num}")
            os.makedirs(chapter_path, exist_ok=True)
            
            verses = fetch_chapter(book_abbr, chapter_num)
            
            if verses:
                # Create full chapter text
                chapter_text = ""
                
                for verse in verses:
                    verse_num = verse.get('verse', 0)
                    verse_text = verse.get('text', '').strip()
                    
                    if verse_num and verse_text:
                        # Save individual verse file
                        verse_file = os.path.join(chapter_path, f"verse-{verse_num}.txt")
                        with open(verse_file, 'w', encoding='utf-8') as f:
                            f.write(verse_text)
                        
                        # Add to chapter text
                        chapter_text += f"{verse_num} {verse_text}\n"
                        
                        # Add to full book text
                        full_book_text += f"{chapter_num}:{verse_num} {verse_text}\n"
                
                # Save full chapter file
                chapter_file = os.path.join(chapter_path, "chapter.txt")
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    f.write(chapter_text)
            
            # Be respectful to the API
            time.sleep(0.5)
        
        # Save the full book file
        book_file = os.path.join(book_path, f"{folder_name}.txt")
        with open(book_file, 'w', encoding='utf-8') as f:
            f.write(full_book_text)
        
        print(f"Saved {folder_name}")

if __name__ == "__main__":
    main()
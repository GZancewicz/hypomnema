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

def fetch_chapter_with_retry(book_abbr, chapter, retries=3):
    """Fetch a single chapter from the API with retries"""
    url = f"https://bible-api.com/{book_abbr}+{chapter}?translation=kjv"
    
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                return data.get('verses', [])
        except urllib.error.HTTPError as e:
            if e.code == 429:  # Too Many Requests
                wait_time = (attempt + 1) * 5  # Exponential backoff
                print(f"    Rate limited, waiting {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"    Error fetching {book_abbr} {chapter}: {e}")
                return None
        except Exception as e:
            print(f"    Unexpected error: {e}")
            return None
    
    print(f"    Failed to fetch {book_abbr} {chapter} after {retries} attempts")
    return None

def main():
    base_path = os.path.join(os.path.dirname(__file__), '..', 'texts', 'english', 'kjv')
    
    # Track overall progress
    total_books = len(books)
    completed_books = 0
    
    for folder_name, book_abbr, num_chapters in books:
        book_file_path = os.path.join(base_path, folder_name, f"{folder_name}.txt")
        
        # Check if book already exists and has content
        if os.path.exists(book_file_path) and os.path.getsize(book_file_path) > 100:
            print(f"✓ {folder_name} already complete")
            completed_books += 1
            continue
        
        print(f"\nProcessing {folder_name} ({completed_books + 1}/{total_books})...")
        
        book_text = ""
        failed_chapters = []
        
        for chapter_num in range(1, num_chapters + 1):
            print(f"  Chapter {chapter_num}/{num_chapters}", end='', flush=True)
            
            verses = fetch_chapter_with_retry(book_abbr, chapter_num)
            
            if verses:
                for verse in verses:
                    verse_num = verse.get('verse', 0)
                    verse_text = verse.get('text', '').strip()
                    
                    if verse_num and verse_text:
                        # Format: chapter:verse text
                        book_text += f"{chapter_num}:{verse_num} {verse_text}\n"
                
                print(" ✓")
            else:
                failed_chapters.append(chapter_num)
                print(" ✗")
            
            # Rate limiting - wait between chapters
            time.sleep(2)
        
        # Save the book if we got any content
        if book_text:
            os.makedirs(os.path.dirname(book_file_path), exist_ok=True)
            with open(book_file_path, 'w', encoding='utf-8') as f:
                f.write(book_text)
            
            if failed_chapters:
                print(f"  Saved {folder_name} (missing chapters: {failed_chapters})")
            else:
                print(f"  ✓ Completed {folder_name}")
                completed_books += 1
        else:
            print(f"  ✗ Failed to fetch any content for {folder_name}")
    
    print(f"\n\nSummary: {completed_books}/{total_books} books completed")

if __name__ == "__main__":
    main()
import subprocess
import time
import sys

def fetch_books_batch(books):
    """Fetch a batch of books"""
    for book_folder, max_chapters, english_name in books:
        print(f"\nFetching {english_name} ({book_folder})...")
        
        cmd = ['python', 'scripts/fetch-septuagint-correct-pattern.py', book_folder, str(max_chapters)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "Successfully fetched" in result.stdout:
                # Extract number of chapters fetched
                import re
                match = re.search(r'Successfully fetched (\d+) chapters', result.stdout)
                if match:
                    chapters_fetched = match.group(1)
                    print(f"✓ Completed {english_name}: {chapters_fetched} chapters")
                else:
                    print(f"✓ Completed {english_name}")
            else:
                print(f"✗ Failed {english_name}")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                    
        except Exception as e:
            print(f"Error processing {english_name}: {e}")
        
        # Small delay between books
        time.sleep(0.5)

def main():
    # Define batches of books
    batches = [
        # Batch 1: Historical Books
        [
            ('vasiliona', 31, '1 Samuel/Kings'),
            ('vasilionb', 24, '2 Samuel/Kings'),
            ('vasiliong', 22, '1 Kings'),
            ('vasiliond', 25, '2 Kings'),
        ],
        # Batch 2: Chronicles and Ezra
        [
            ('paralipomenona', 29, '1 Chronicles'),
            ('paralipomenonb', 36, '2 Chronicles'),
            ('esdrasa', 10, 'Ezra 1'),
            ('esdrasb', 10, 'Ezra 2'),
        ],
        # Batch 3: Deuterocanonical Historical
        [
            ('tovit', 14, 'Tobit'),
            ('ioudith', 16, 'Judith'),
            ('esthir', 16, 'Esther'),
            ('makkavaiona', 16, '1 Maccabees'),
            ('makkavaionb', 15, '2 Maccabees'),
            ('makkavaiong', 7, '3 Maccabees'),
            ('makkavaiond', 18, '4 Maccabees'),
        ],
        # Batch 4: Wisdom Books
        [
            ('iov', 42, 'Job'),
            ('parimiai', 31, 'Proverbs'),
            ('ekklhsiastis', 12, 'Ecclesiastes'),
            ('asma_asmaton', 8, 'Song of Songs'),
            ('sofia', 19, 'Wisdom'),
            ('sofia_sirah', 51, 'Sirach'),
        ],
        # Batch 5: Minor Prophets 1
        [
            ('osie', 14, 'Hosea'),
            ('amos', 9, 'Amos'),
            ('miheas', 7, 'Micah'),
            ('iohl', 4, 'Joel'),
            ('ovdiou', 1, 'Obadiah'),
            ('ionas', 4, 'Jonah'),
        ],
        # Batch 6: Minor Prophets 2
        [
            ('naoum', 3, 'Nahum'),
            ('amvakoum', 3, 'Habakkuk'),
            ('sofonias', 3, 'Zephaniah'),
            ('aggaios', 2, 'Haggai'),
            ('zaharias', 14, 'Zechariah'),
            ('malahias', 4, 'Malachi'),
        ],
        # Batch 7: Major Prophets
        [
            ('ieremias', 52, 'Jeremiah'),
            ('varouh', 6, 'Baruch'),
            ('thrinoi', 5, 'Lamentations'),
            ('epistoli_ier', 1, 'Letter of Jeremiah'),
            ('iezekihl', 48, 'Ezekiel'),
        ]
    ]
    
    if len(sys.argv) > 1:
        batch_num = int(sys.argv[1]) - 1
        if 0 <= batch_num < len(batches):
            print(f"Fetching Batch {batch_num + 1}")
            print("=" * 60)
            fetch_books_batch(batches[batch_num])
        else:
            print(f"Invalid batch number. Choose 1-{len(batches)}")
    else:
        print("Usage: python fetch-septuagint-batch.py <batch_number>")
        print(f"\nAvailable batches (1-{len(batches)}):")
        for i, batch in enumerate(batches, 1):
            print(f"\nBatch {i}:")
            for _, _, name in batch:
                print(f"  - {name}")

if __name__ == "__main__":
    main()
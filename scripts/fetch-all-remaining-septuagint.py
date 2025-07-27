import subprocess
import time
import os
import json

def get_remaining_books():
    """Get list of remaining books to fetch"""
    return [
        ('vasiliona', 31, '1 Samuel/Kings'),
        ('vasilionb', 24, '2 Samuel/Kings'),
        ('vasiliong', 22, '1 Kings'),
        ('vasiliond', 25, '2 Kings'),
        ('paralipomenona', 29, '1 Chronicles'),
        ('paralipomenonb', 36, '2 Chronicles'),
        ('esdrasa', 10, 'Ezra 1'),
        ('esdrasb', 10, 'Ezra 2'),
        ('neemias', 13, 'Nehemiah'),
        ('tovit', 14, 'Tobit'),
        ('ioudith', 16, 'Judith'),
        ('esthir', 16, 'Esther'),
        ('makkavaiona', 16, '1 Maccabees'),
        ('makkavaionb', 15, '2 Maccabees'),
        ('makkavaiong', 7, '3 Maccabees'),
        ('iov', 42, 'Job'),
        ('parimiai', 31, 'Proverbs'),
        ('ekklhsiastis', 12, 'Ecclesiastes'),
        ('asma_asmaton', 8, 'Song of Songs'),
        ('sofia', 19, 'Wisdom'),
        ('sofia_sirah', 51, 'Sirach'),
        ('osie', 14, 'Hosea'),
        ('amos', 9, 'Amos'),
        ('miheas', 7, 'Micah'),
        ('iohl', 4, 'Joel'),
        ('ovdiou', 1, 'Obadiah'),
        ('ionas', 4, 'Jonah'),
        ('naoum', 3, 'Nahum'),
        ('amvakoum', 3, 'Habakkuk'),
        ('sofonias', 3, 'Zephaniah'),
        ('aggaios', 2, 'Haggai'),
        ('zaharias', 14, 'Zechariah'),
        ('malahias', 4, 'Malachi'),
        ('ieremias', 52, 'Jeremiah'),
        ('varouh', 6, 'Baruch'),
        ('thrinoi', 5, 'Lamentations'),
        ('epistoli_ier', 1, 'Letter of Jeremiah'),
        ('iezekihl', 48, 'Ezekiel'),
        ('makkavaiond', 18, '4 Maccabees')
    ]

def main():
    print("Fetching All Remaining Greek Septuagint Books")
    print("=" * 60)
    
    books = get_remaining_books()
    total_books = len(books)
    
    # Track progress
    progress_file = 'septuagint_fetch_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}
    
    successful = 0
    failed = []
    
    start_time = time.time()
    
    for i, (book_folder, max_chapters, english_name) in enumerate(books, 1):
        # Skip if already completed
        if book_folder in progress and progress[book_folder].get('status') == 'completed':
            print(f"[{i}/{total_books}] {english_name} - Already completed")
            successful += 1
            continue
        
        print(f"\n[{i}/{total_books}] Fetching {english_name} ({book_folder})...")
        
        # Run the fetch script
        cmd = ['python', 'scripts/fetch-septuagint-correct-pattern.py', book_folder, str(max_chapters)]
        
        try:
            # Run with a timeout based on chapter count (3 seconds per chapter max)
            timeout = min(max_chapters * 3, 300)  # Max 5 minutes
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if "Successfully fetched" in result.stdout:
                print(f"✓ Completed {english_name}")
                progress[book_folder] = {
                    'status': 'completed', 
                    'english_name': english_name,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                successful += 1
            else:
                print(f"✗ Failed {english_name}")
                print(f"  Error: {result.stderr[:200] if result.stderr else 'Unknown error'}")
                progress[book_folder] = {
                    'status': 'failed',
                    'english_name': english_name,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                failed.append(english_name)
            
            # Save progress after each book
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
                
        except subprocess.TimeoutExpired:
            print(f"⚠ Timeout for {english_name}")
            progress[book_folder] = {
                'status': 'timeout',
                'english_name': english_name,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            failed.append(english_name)
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Progress saved.")
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
            break
        except Exception as e:
            print(f"Error processing {english_name}: {e}")
            failed.append(english_name)
        
        # Small delay between books
        time.sleep(1)
    
    # Final summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total books: {total_books}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(failed)}")
    print(f"  Time elapsed: {elapsed_time/60:.1f} minutes")
    
    if failed:
        print(f"\nFailed books:")
        for book in failed:
            print(f"  - {book}")
    
    print(f"\nProgress saved to: {progress_file}")

if __name__ == "__main__":
    main()
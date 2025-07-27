import os
import json
import subprocess
import time

def get_book_info():
    """Get book info with estimated chapter counts"""
    return [
        ('genesis', 50),
        ('exodos', 40),
        ('levitikon', 27),
        ('arithmoi', 36),
        ('defteronomion', 34),
        ('navi', 24),
        ('kritai', 21),
        ('routh', 4),
        ('vasiliona', 31),
        ('vasilionb', 24),
        ('vasiliong', 22),
        ('vasiliond', 25),
        ('paralipomenona', 29),
        ('paralipomenonb', 36),
        ('esdrasa', 10),
        ('esdrasb', 10),
        ('neemias', 13),
        ('tovit', 14),
        ('ioudith', 16),
        ('esthir', 16),
        ('makkavaiona', 16),
        ('makkavaionb', 15),
        ('makkavaiong', 7),
        ('psalmoi', 151),
        ('iov', 42),
        ('parimiai', 31),
        ('ekklhsiastis', 12),
        ('asma_asmaton', 8),
        ('sofia', 19),
        ('sofia_sirah', 51),
        ('osie', 14),
        ('amos', 9),
        ('miheas', 7),
        ('iohl', 4),
        ('ovdiou', 1),
        ('ionas', 4),
        ('naoum', 3),
        ('amvakoum', 3),
        ('sofonias', 3),
        ('aggaios', 2),
        ('zaharias', 14),
        ('malahias', 4),
        ('hsaias', 66),
        ('ieremias', 52),
        ('varouh', 6),
        ('thrinoi', 5),
        ('epistoli_ier', 1),
        ('iezekihl', 48),
        ('danihl', 14),
        ('makkavaiond', 18)
    ]

def main():
    print("Fetching Complete Greek Septuagint")
    print("=" * 60)
    
    books = get_book_info()
    total_books = len(books)
    
    # Track progress
    progress_file = 'septuagint_progress.json'
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {}
    
    successful = 0
    failed = []
    
    for i, (book_folder, max_chapters) in enumerate(books, 1):
        # Skip if already completed
        if book_folder in progress and progress[book_folder].get('status') == 'completed':
            print(f"[{i}/{total_books}] {book_folder} - Already completed")
            successful += 1
            continue
        
        print(f"\n[{i}/{total_books}] Fetching {book_folder}...")
        
        # Run the fetch script
        cmd = ['python', 'scripts/fetch-septuagint-correct-pattern.py', book_folder, str(max_chapters)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if "Successfully fetched" in result.stdout:
                print(f"✓ Completed {book_folder}")
                progress[book_folder] = {'status': 'completed', 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
                successful += 1
            else:
                print(f"✗ Failed {book_folder}")
                progress[book_folder] = {'status': 'failed', 'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')}
                failed.append(book_folder)
            
            # Save progress after each book
            with open(progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Progress saved.")
            break
        except Exception as e:
            print(f"Error processing {book_folder}: {e}")
            failed.append(book_folder)
        
        # Small delay between books
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  Total books: {total_books}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed books: {', '.join(failed)}")
    
    print(f"\nProgress saved to: {progress_file}")

if __name__ == "__main__":
    main()
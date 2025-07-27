import os
import json
import subprocess
import time

def load_book_mapping():
    """Load the book mapping from JSON file"""
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    
    if os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def main():
    print("Testing Greek Septuagint Availability")
    print("=" * 50)
    
    mapping = load_book_mapping()
    results = {}
    
    # Test first 3 chapters of each book
    for folder_name, info in sorted(mapping.items()):
        print(f"\nTesting {info['greek_name']} ({folder_name})...")
        
        # Run the fetch script
        cmd = ['python', 'scripts/fetch-septuagint-single-book.py', folder_name, '3']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Check if any chapters were fetched
            if "Successfully fetched" in result.stdout:
                # Extract number of chapters
                import re
                match = re.search(r'Successfully fetched (\d+) chapters', result.stdout)
                if match:
                    chapters = int(match.group(1))
                    print(f"  ✓ Found {chapters} chapter(s)")
                    results[folder_name] = {
                        'greek_name': info['greek_name'],
                        'chapters_found': chapters,
                        'status': 'available'
                    }
            else:
                print(f"  ✗ No chapters found")
                results[folder_name] = {
                    'greek_name': info['greek_name'],
                    'chapters_found': 0,
                    'status': 'unavailable'
                }
                
        except subprocess.TimeoutExpired:
            print(f"  ⚠ Timeout")
            results[folder_name] = {
                'greek_name': info['greek_name'],
                'chapters_found': 0,
                'status': 'timeout'
            }
        except Exception as e:
            print(f"  ⚠ Error: {e}")
            results[folder_name] = {
                'greek_name': info['greek_name'],
                'chapters_found': 0,
                'status': 'error'
            }
        
        # Small delay between books
        time.sleep(1)
    
    # Save results
    results_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                'texts', 'scripture', 'greek', 'septuagint', 'availability_test.json')
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY:")
    available = [k for k, v in results.items() if v['status'] == 'available']
    print(f"  Available books: {len(available)}")
    
    if available:
        print("\nBooks with content:")
        for book in available:
            print(f"  - {results[book]['greek_name']} ({book}): {results[book]['chapters_found']} chapters")
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main()
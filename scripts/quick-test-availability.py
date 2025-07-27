import os
import urllib.request
import json
import time
from html.parser import HTMLParser

class QuickParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.has_greek = False
        
    def handle_data(self, data):
        if not self.has_greek and len(data) > 20:
            # Check for Greek characters
            if any('\u0370' <= char <= '\u03ff' or '\u1f00' <= char <= '\u1fff' for char in data):
                self.has_greek = True

def quick_test_book(url_name, chapter=1, verse=1):
    """Quick test if a book/chapter has content"""
    url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{url_name}.asp&main={url_name.lower()}&file={chapter}.{verse}.htm"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        with urllib.request.urlopen(req, timeout=3) as response:
            raw_data = response.read()
            try:
                content = raw_data.decode('iso-8859-7')
            except:
                content = raw_data.decode('utf-8', errors='ignore')
            
            parser = QuickParser()
            parser.feed(content)
            return parser.has_greek
            
    except:
        return False

def main():
    print("Quick Test of Greek Septuagint Availability")
    print("=" * 50)
    
    # Load book mapping
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    mapping_file = os.path.join(base_dir, 'book_mapping.json')
    
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    
    available = []
    
    print("\nTesting books (checking chapter 1, verse 1)...")
    for folder_name, info in sorted(mapping.items()):
        print(f"  {info['greek_name']:<30} ", end='', flush=True)
        
        # Test chapter 1
        if quick_test_book(info['url_name'], 1, 1):
            print("✓ Chapter 1 available")
            available.append((folder_name, info['greek_name'], info['url_name']))
        else:
            # Try chapter 2
            if quick_test_book(info['url_name'], 2, 1):
                print("✓ Chapter 2 available")
                available.append((folder_name, info['greek_name'], info['url_name']))
            else:
                print("✗ Not available")
        
        time.sleep(0.2)  # Small delay
    
    print(f"\n{'='*50}")
    print(f"Found {len(available)} books with content:")
    for folder, greek, url in available:
        print(f"  {greek} ({folder})")
    
    # Save results
    results_file = os.path.join(base_dir, 'available_books.json')
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump([{'folder': f, 'greek_name': g, 'url_name': u} for f, g, u in available], 
                  f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    main()
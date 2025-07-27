import urllib.request
import time

def test_url_patterns(book_name, url_variations, seq_numbers):
    """Test different URL patterns for a book"""
    print(f"\nTesting {book_name}...")
    
    for url_var in url_variations:
        for seq in seq_numbers:
            # Test chapter 1, verse 1
            url = f"https://apostoliki-diakonia.gr/bible/bible.asp?contents=old_testament/contents_{url_var}.asp&main={url_var.lower()}&file={seq}.1.htm"
            
            try:
                req = urllib.request.Request(url)
                req.add_header('User-Agent', 'Mozilla/5.0')
                
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        # Check if content has Greek text
                        content = response.read()
                        try:
                            decoded = content.decode('iso-8859-7')
                        except:
                            decoded = content.decode('utf-8', errors='ignore')
                        
                        # Look for Greek characters
                        if any('\u0370' <= char <= '\u03ff' or '\u1f00' <= char <= '\u1fff' for char in decoded):
                            print(f"  ✓ Found! URL pattern: {url_var}, Sequence: {seq}")
                            print(f"    URL: {url}")
                            return url_var, seq
                            
            except Exception as e:
                pass
            
            time.sleep(0.2)
    
    print(f"  ✗ No working pattern found")
    return None, None

def main():
    # Test patterns for the missing books
    missing_books = [
        # Book name, URL variations to try, sequence numbers to try
        ("1 Samuel/Kings", ["VasilionA", "Vasilion_A", "BasilionA", "Basilion_A"], [9, 10, 11]),
        ("2 Samuel/Kings", ["VasilionB", "Vasilion_B", "BasilionB", "Basilion_B"], [10, 11, 12]),
        ("1 Kings", ["VasilionG", "Vasilion_G", "BasilionG", "Basilion_G"], [11, 12, 13]),
        ("2 Kings", ["VasilionD", "Vasilion_D", "BasilionD", "Basilion_D"], [12, 13, 14]),
        ("1 Chronicles", ["ParalipomenonA", "Paralipomenon_A", "ParaleipomenonA"], [13, 14, 15]),
        ("2 Chronicles", ["ParalipomenonB", "Paralipomenon_B", "ParaleipomenonB"], [14, 15, 16]),
        ("1 Ezra", ["EsdrasA", "Esdras_A", "EzraA"], [15, 16, 17]),
        ("2 Ezra", ["EsdrasB", "Esdras_B", "EzraB"], [16, 17, 18]),
        ("1 Maccabees", ["MakkavaionA", "Makkavaion_A", "MaccabeesA"], [21, 22, 23]),
        ("2 Maccabees", ["MakkavaionB", "Makkavaion_B", "MaccabeesB"], [22, 23, 24]),
        ("3 Maccabees", ["MakkavaionG", "Makkavaion_G", "makkavaionG"], [23, 24, 25]),
        ("4 Maccabees", ["MakkavaionD", "Makkavaion_D", "makkavaionD"], [50, 51, 52])
    ]
    
    results = {}
    
    for book_name, url_vars, seq_nums in missing_books:
        url_pattern, seq_num = test_url_patterns(book_name, url_vars, seq_nums)
        if url_pattern:
            results[book_name] = {
                'url_pattern': url_pattern,
                'sequence': seq_num
            }
    
    print("\n" + "="*60)
    print("Results:")
    for book, info in results.items():
        print(f"{book}: URL={info['url_pattern']}, Seq={info['sequence']}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import os

def check_book_completeness():
    """Check which books have missing chapters"""
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia')
    
    # Expected chapters for each book
    expected_chapters = {
        'Genesis': 50,
        'Exodos': 40,
        'Levitikon': 27,
        'Arithmoi': 36,
        'Defteronomion': 34,
        'Navi': 24,
        'Kritai': 21,
        'Routh': 4,
        'VasilionA': 31,
        'VasilionB': 24,
        'VasilionG': 22,
        'VasilionD': 25,
        'ParalipomenonA': 29,
        'ParalipomenonB': 36,
        'EsdrasA': 10,
        'EsdrasB': 10,
        'Neemias': 13,
        'Tovit': 14,
        'Ioudith': 16,
        'Esthir': 10,
        'MakkavaionA': 16,
        'MakkavaionB': 15,
        'makkavaionG': 7,
        'Psalmoi': 151,
        'Iov': 42,
        'Parimiai': 31,
        'Ekklhsiastis': 12,
        'Asma_Asmaton': 8,
        'Sofia': 19,
        'Sofia_Sirah': 51,
        'Osie': 14,
        'Amos': 9,
        'Miheas': 7,
        'Iohl': 3,
        'Ovdiou': 1,
        'Ionas': 4,
        'Naoum': 3,
        'Amvakoum': 3,
        'Sofonias': 3,
        'Aggaios': 2,
        'Zaharias': 14,
        'Malahias': 4,
        'Hsaias': 66,
        'Ieremias': 52,
        'Varouh': 5,
        'Thrinoi': 5,
        'Epistoli_Ier': 1,
        'Iezekihl': 48,
        'Danihl': 12,
        'makkavaionD': 18
    }
    
    incomplete_books = []
    missing_books = []
    complete_books = []
    
    for book, expected in expected_chapters.items():
        book_path = os.path.join(base_dir, book)
        
        if not os.path.exists(book_path):
            missing_books.append((book, expected))
            continue
            
        # Check how many chapters exist
        chapters = []
        for item in os.listdir(book_path):
            if item.isdigit():
                chapters.append(int(item))
        
        if not chapters:
            missing_books.append((book, expected))
        elif len(chapters) < expected:
            # Find which chapters are missing
            missing_chapters = []
            for i in range(1, expected + 1):
                if i not in chapters:
                    missing_chapters.append(i)
            incomplete_books.append((book, expected, len(chapters), missing_chapters))
        else:
            complete_books.append((book, expected))
    
    # Print report
    print("Book Status Report")
    print("=" * 80)
    
    print(f"\nComplete Books ({len(complete_books)}):")
    for book, chapters in sorted(complete_books):
        print(f"  ✓ {book}: {chapters} chapters")
    
    print(f"\nIncomplete Books ({len(incomplete_books)}):")
    for book, expected, actual, missing in sorted(incomplete_books):
        print(f"  ⚠ {book}: {actual}/{expected} chapters")
        if len(missing) <= 10:
            print(f"     Missing chapters: {', '.join(map(str, missing))}")
        else:
            print(f"     Missing {len(missing)} chapters")
    
    print(f"\nCompletely Missing Books ({len(missing_books)}):")
    for book, expected in sorted(missing_books):
        print(f"  ✗ {book}: 0/{expected} chapters")
    
    print("\nSummary:")
    print(f"  Total books: {len(expected_chapters)}")
    print(f"  Complete: {len(complete_books)}")
    print(f"  Incomplete: {len(incomplete_books)}")
    print(f"  Missing: {len(missing_books)}")

if __name__ == "__main__":
    check_book_completeness()
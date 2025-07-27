#!/usr/bin/env python3
import os

def create_all_book_folders():
    """Create folders for all 50 books from the apostoliki-diakonia.gr website"""
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'old_testament', 'greek', 'apostoliki_diakonia')
    
    # All 50 books from the HTML in exact order
    all_books = [
        'Genesis',           # ΓΕΝΕΣΙΣ
        'Exodos',            # ΕΞΟΔΟΣ
        'Levitikon',         # ΛΕΥΙΤΙΚΟΝ
        'Arithmoi',          # ΑΡΙΘΜΟΙ
        'Defteronomion',     # ΔΕΥΤΕΡΟΝΟΜΙΟΝ
        'Navi',              # ΙΗΣΟΥΣ ΝΑΥΗ
        'Kritai',            # ΚΡΙΤΑΙ
        'Routh',             # ΡΟΥΘ
        'VasilionA',         # ΒΑΣΙΛΕΙΩΝ Α'
        'VasilionB',         # ΒΑΣΙΛΕΙΩΝ Β'
        'VasilionG',         # ΒΑΣΙΛΕΙΩΝ Γ'
        'VasilionD',         # ΒΑΣΙΛΕΙΩΝ Δ'
        'ParalipomenonA',    # ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Α'
        'ParalipomenonB',    # ΠΑΡΑΛΕΙΠΟΜΕΝΩΝ Β'
        'EsdrasA',           # ΕΣΔΡΑΣ Α'
        'EsdrasB',           # ΕΣΔΡΑΣ Β'
        'Neemias',           # ΝΕΕΜΙΑΣ
        'Tovit',             # ΤΩΒΙΤ
        'Ioudith',           # ΙΟΥΔΙΘ
        'Esthir',            # ΕΣΘΗΡ
        'MakkavaionA',       # ΜΑΚΚΑΒΑΙΩΝ Α'
        'MakkavaionB',       # ΜΑΚΚΑΒΑΙΩΝ Β'
        'makkavaionG',       # ΜΑΚΚΑΒΑΙΩΝ Γ' (lowercase G)
        'Psalmoi',           # ΨΑΛΜΟΙ
        'Iov',               # ΙΩΒ
        'Parimiai',          # ΠΑΡΟΙΜΙΑΙ ΣΟΛΟΜΩΝΤΟΣ
        'Ekklhsiastis',      # ΕΚΚΛΗΣΙΑΣΤΗΣ
        'Asma_Asmaton',      # ΑΣΜΑ ΑΣΜΑΤΩΝ
        'Sofia',             # ΣΟΦΙΑ ΣΟΛΟΜΩΝΤΟΣ
        'Sofia_Sirah',       # ΣΟΦΙΑ ΣΕΙΡΑΧ
        'Osie',              # ΩΣΗΕ
        'Amos',              # ΑΜΩΣ
        'Miheas',            # ΜΙΧΑΙΑΣ
        'Iohl',              # ΙΩΗΛ
        'Ovdiou',            # ΟΒΔΙΟΥ
        'Ionas',             # ΙΩΝΑΣ
        'Naoum',             # ΝΑΟΥΜ
        'Amvakoum',          # ΑΜΒΑΚΟΥΜ
        'Sofonias',          # ΣΟΦΟΝΙΑΣ
        'Aggaios',           # ΑΓΓΑΙΟΣ
        'Zaharias',          # ΖΑΧΑΡΙΑΣ
        'Malahias',          # ΜΑΛΑΧΙΑΣ
        'Hsaias',            # ΗΣΑΪΑΣ
        'Ieremias',          # ΙΕΡΕΜΙΑΣ
        'Varouh',            # ΒΑΡΟΥΧ
        'Thrinoi',           # ΘΡΗΝΟΙ ΙΕΡΕΜΙΟΥ
        'Epistoli_Ier',      # ΕΠΙΣΤΟΛΗ ΙΕΡΕΜΙΟΥ
        'Iezekihl',          # ΙΕΖΕΚΙΗΛ
        'Danihl',            # ΔΑΝΙΗΛ
        'makkavaionD'        # ΜΑΚΚΑΒΑΙΩΝ Δ' ΠΑΡΑΡΤΗΜΑ (lowercase D)
    ]
    
    # Create base directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)
    
    # Check existing folders
    existing_folders = set(os.listdir(base_dir))
    
    # Create missing folders
    created = []
    already_exist = []
    
    for book in all_books:
        book_path = os.path.join(base_dir, book)
        if book not in existing_folders:
            os.makedirs(book_path, exist_ok=True)
            created.append(book)
        else:
            already_exist.append(book)
    
    print("Book Folder Status")
    print("=" * 60)
    print(f"Total books in HTML: {len(all_books)}")
    print(f"Already exist: {len(already_exist)}")
    print(f"Created new: {len(created)}")
    
    if created:
        print("\nNewly created folders:")
        for book in created:
            print(f"  - {book}")
    
    # Show which ones have content
    print("\nChecking which folders have content...")
    empty_folders = []
    folders_with_content = []
    
    for book in all_books:
        book_path = os.path.join(base_dir, book)
        if os.path.exists(book_path):
            contents = os.listdir(book_path)
            # Check if it has chapter folders with content
            has_content = False
            for item in contents:
                item_path = os.path.join(book_path, item)
                if os.path.isdir(item_path) and item.isdigit():
                    # Check if chapter folder has any .txt files
                    chapter_files = os.listdir(item_path)
                    if any(f.endswith('.txt') for f in chapter_files):
                        has_content = True
                        break
            
            if has_content:
                folders_with_content.append(book)
            else:
                empty_folders.append(book)
    
    print(f"\nFolders with content: {len(folders_with_content)}")
    print(f"Empty folders (need fetching): {len(empty_folders)}")
    
    print("\nEmpty folders that need content:")
    for i, book in enumerate(empty_folders, 1):
        print(f"  {i:2d}. {book}")

if __name__ == "__main__":
    create_all_book_folders()
#!/usr/bin/env python3
import os
import shutil

def rename_folders():
    """Rename Septuagint folders to match the HTML element names from apostoliki-diakonia.gr"""
    
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    # Mapping of current folder names to new names based on HTML
    rename_map = {
        # These need to be created/renamed based on the HTML
        'Navi': 'Navi',
        'Kritai': 'Kritai', 
        'Routh': 'Routh',
        'Tovit': 'Tovit',
        'Ioudith': 'Ioudith',
        'Esthir': 'Esthir',
        'Psalmoi': 'Psalmoi',
        'Iov': 'Iov',
        'Parimiai': 'Parimiai',
        'Ekklhsiastis': 'Ekklhsiastis',
        'Asma_Asmaton': 'Asma_Asmaton',
        'Sofia': 'Sofia',
        'Sofia_Sirah': 'Sofia_Sirah',
        'Osie': 'Osie',
        'Amos': 'Amos',
        'Miheas': 'Miheas',
        'Iohl': 'Iohl',
        'Ovdiou': 'Ovdiou',
        'Ionas': 'Ionas',
        'Naoum': 'Naoum',
        'Amvakoum': 'Amvakoum',
        'Sofonias': 'Sofonias',
        'Aggaios': 'Aggaios',
        'Zaharias': 'Zaharias',
        'Malahias': 'Malahias',
        'Hsaias': 'Hsaias',
        'Ieremias': 'Ieremias',
        'Varouh': 'Varouh',
        'Thrinoi': 'Thrinoi',
        'Epistoli_Ier': 'Epistoli_Ier',
        'Iezekihl': 'Iezekihl',
        'Danihl': 'Danihl'
    }
    
    # Check existing folders and identify what needs to be done
    existing_folders = set(os.listdir(base_dir))
    
    print("Current folders in septuagint directory:")
    for folder in sorted(existing_folders):
        if os.path.isdir(os.path.join(base_dir, folder)):
            print(f"  - {folder}")
    
    print("\nFolders that need to be created/fetched based on HTML:")
    html_books = set(rename_map.values())
    missing_books = html_books - existing_folders
    
    for book in sorted(missing_books):
        print(f"  - {book}")
    
    # Show the folder structure expected based on HTML
    print("\nComplete list of books from HTML (in order):")
    html_order = [
        'Genesis', 'Exodos', 'Levitikon', 'Arithmoi', 'Defteronomion',
        'Navi', 'Kritai', 'Routh', 'VasilionA', 'VasilionB', 'VasilionG', 'VasilionD',
        'ParalipomenonA', 'ParalipomenonB', 'EsdrasA', 'EsdrasB', 'Neemias',
        'Tovit', 'Ioudith', 'Esthir', 'MakkavaionA', 'MakkavaionB', 'makkavaionG',
        'Psalmoi', 'Iov', 'Parimiai', 'Ekklhsiastis', 'Asma_Asmaton',
        'Sofia', 'Sofia_Sirah', 'Osie', 'Amos', 'Miheas', 'Iohl', 'Ovdiou',
        'Ionas', 'Naoum', 'Amvakoum', 'Sofonias', 'Aggaios', 'Zaharias',
        'Malahias', 'Hsaias', 'Ieremias', 'Varouh', 'Thrinoi', 'Epistoli_Ier',
        'Iezekihl', 'Danihl', 'makkavaionD'
    ]
    
    for i, book in enumerate(html_order, 1):
        status = "✓" if book in existing_folders else "✗"
        print(f"  {i:2d}. {status} {book}")

if __name__ == "__main__":
    rename_folders()
#!/usr/bin/env python3
"""Add 'end' key to Chrysostom homily metadata.json files based on text analysis"""

import json
import os
import re
from pathlib import Path

def extract_ending_verse_from_homily(homily_file_path):
    """
    Extract the ending verse reference from a homily text file.
    Looks for the last Matthew reference in the format "Matthew I. 1", "Matthew II. 1", etc.
    """
    try:
        with open(homily_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for all Matthew references in the format "Matthew I. 1", "Matthew II. 1", etc.
        # Pattern matches: Matthew + Roman numeral + period + verse number(s)
        pattern = r'Matthew\s+([IVX]+)\.\s*(\d+(?:,\s*\d+)*)'
        matches = re.findall(pattern, content, re.IGNORECASE)
        
        if not matches:
            return ""
        
        # Get the last match
        last_match = matches[-1]
        roman_chapter = last_match[0]
        verse_numbers = last_match[1]
        
        # Convert Roman numeral to Arabic number
        roman_to_arabic = {
            'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 
            'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
            'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21,
            'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25, 'XXVI': 26, 'XXVII': 27, 'XXVIII': 28
        }
        
        chapter_num = roman_to_arabic.get(roman_chapter, 0)
        if chapter_num == 0:
            return ""
        
        # Handle multiple verse numbers (e.g., "1, 2")
        if ',' in verse_numbers:
            # Take the last verse number
            verse_parts = verse_numbers.split(',')
            last_verse = verse_parts[-1].strip()
        else:
            last_verse = verse_numbers.strip()
        
        return f"Matthew {chapter_num}:{last_verse}"
        
    except Exception as e:
        print(f"Error processing {homily_file_path}: {e}")
        return ""

def update_metadata_files():
    """Update all metadata.json files with 'end' key"""
    
    homilies_dir = Path('texts/commentaries/chrysostom/matthew/homilies')
    
    if not homilies_dir.exists():
        print(f"Directory not found: {homilies_dir}")
        return
    
    updated_count = 0
    skipped_count = 0
    
    # Process each homily directory
    for homily_dir in sorted(homilies_dir.iterdir()):
        if not homily_dir.is_dir():
            continue
        
        metadata_file = homily_dir / 'metadata.json'
        if not metadata_file.exists():
            print(f"No metadata.json found in {homily_dir}")
            continue
        
        # Find the homily text file
        homily_text_file = None
        for txt_file in homily_dir.glob('*.txt'):
            if 'homily' in txt_file.name.lower():
                homily_text_file = txt_file
                break
        
        if not homily_text_file:
            print(f"No homily text file found in {homily_dir}")
            continue
        
        # Load existing metadata
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Error reading {metadata_file}: {e}")
            continue
        
        # Skip if 'end' key already exists
        if 'end' in metadata:
            print(f"Skipping {homily_dir.name} - 'end' key already exists")
            skipped_count += 1
            continue
        
        # Extract ending verse
        ending_verse = extract_ending_verse_from_homily(homily_text_file)
        
        # Add the 'end' key
        metadata['end'] = ending_verse
        
        # Write updated metadata
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"Updated {homily_dir.name}: passage='{metadata.get('passage', '')}' -> end='{ending_verse}'")
            updated_count += 1
            
        except Exception as e:
            print(f"Error writing {metadata_file}: {e}")
    
    print(f"\nSummary:")
    print(f"Updated: {updated_count} files")
    print(f"Skipped: {skipped_count} files")

def main():
    print("Adding 'end' key to Chrysostom homily metadata files...")
    print("=" * 60)
    
    # Change to the project root directory
    os.chdir('/Users/gregzancewicz/Documents/Other/Projects/hypomnema')
    
    update_metadata_files()
    
    print("\nDone!")

if __name__ == "__main__":
    main()
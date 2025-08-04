#!/usr/bin/env python3
"""Generate mapping of Matthew verses to Chrysostom homilies"""

import json
import os
from pathlib import Path

def parse_verse_reference(verse_ref):
    """Parse a verse reference like 'Matthew 1:1' into chapter and verse"""
    if not verse_ref or verse_ref == "Matthew (Introduction)":
        return None, None
    
    parts = verse_ref.replace("Matthew ", "").split(":")
    if len(parts) == 2:
        try:
            chapter = int(parts[0])
            verse = int(parts[1])
            return chapter, verse
        except ValueError:
            return None, None
    return None, None

def to_roman(num):
    """Convert number to Roman numeral"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        'M', 'CM', 'D', 'CD',
        'C', 'XC', 'L', 'XL',
        'X', 'IX', 'V', 'IV',
        'I'
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def main():
    print("Generating verse-to-homily mapping for Matthew...")
    
    homilies_dir = Path('texts/commentaries/chrysostom/matthew/homilies')
    
    if not homilies_dir.exists():
        print(f"Directory not found: {homilies_dir}")
        return
    
    # This will hold the mapping of chapter:verse -> homily info
    verse_to_homily = {}
    
    # Process each homily directory
    for homily_dir in sorted(homilies_dir.iterdir()):
        if not homily_dir.is_dir():
            continue
        
        metadata_file = homily_dir / 'metadata.json'
        if not metadata_file.exists():
            continue
        
        # Load metadata
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Error reading {metadata_file}: {e}")
            continue
        
        # Get homily number and convert to Roman numerals
        section = metadata.get('section', 0)
        if section == 0:
            continue
        
        roman_num = to_roman(section)
        
        # Get starting verse
        passage = metadata.get('passage', '')
        chapter, verse = parse_verse_reference(passage)
        
        if chapter is not None and verse is not None:
            verse_key = f"{chapter}:{verse}"
            
            # Store the homily reference
            verse_to_homily[verse_key] = {
                "homily_number": section,
                "homily_roman": roman_num,
                "passage": passage,
                "end": metadata.get('end', '')
            }
            
            print(f"Homily {roman_num} ({section}): {passage}")
    
    # Save to JSON
    output_file = Path('texts/reference/chrysostom_homilies/matthew_verse_to_homily.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(verse_to_homily, f, indent=2, sort_keys=True)
    
    print(f"\nSaved {len(verse_to_homily)} verse mappings to {output_file}")
    
    # Show sample
    print("\nSample mappings:")
    for key in sorted(list(verse_to_homily.keys())[:5]):
        info = verse_to_homily[key]
        print(f"  {key} -> Homily {info['homily_roman']}")

if __name__ == "__main__":
    # Change to project root
    os.chdir('/Users/gregzancewicz/Documents/Other/Projects/hypomnema')
    main()
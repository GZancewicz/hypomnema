#!/usr/bin/env python3
"""
Extract John homilies and create verse-to-homily mapping
"""

import xml.etree.ElementTree as ET
import json
import re
import os

def roman_to_arabic(roman):
    """Convert Roman numerals to Arabic numbers"""
    roman_dict = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100
    }
    
    i = 0
    num = 0
    while i < len(roman):
        if i + 1 < len(roman) and roman[i] in roman_dict and roman[i + 1] in roman_dict:
            if roman_dict[roman[i]] < roman_dict[roman[i + 1]]:
                num += roman_dict[roman[i + 1]] - roman_dict[roman[i]]
                i += 2
            else:
                num += roman_dict[roman[i]]
                i += 1
        else:
            if roman[i] in roman_dict:
                num += roman_dict[roman[i]]
            i += 1
    return num

def parse_verse_reference(ref):
    """Parse a John verse reference like 'John 1.1' or 'John 1.35-37'"""
    # Remove 'John' prefix
    ref = ref.replace('John', '').strip()
    
    # Handle special case "John 13" (whole chapter)
    if ref.isdigit():
        chapter = int(ref)
        return chapter, 1, 1  # Default to verse 1
    
    # Handle verse ranges like "1.35-37" or "1.35—37"
    if '—' in ref or '-' in ref:
        # Split on dash
        parts = re.split(r'[—-]', ref)
        if len(parts) == 2:
            start = parts[0].strip()
            end = parts[1].strip()
            
            # Parse start (e.g., "1.35")
            if '.' in start:
                chapter, start_verse = start.split('.')
                chapter = int(chapter)
                start_verse = int(start_verse)
                
                # Parse end (might be just verse number)
                if '.' in end:
                    _, end_verse = end.split('.')
                    end_verse = int(end_verse)
                else:
                    end_verse = int(end)
                
                return chapter, start_verse, end_verse
    
    # Handle semicolon-separated chapters like "4.54; 5.1"
    elif ';' in ref:
        # Take the first reference
        ref = ref.split(';')[0].strip()
    
    # Handle comma-separated verses like "1.28,29"
    elif ',' in ref:
        # For now, just take the first verse
        ref = ref.split(',')[0].strip()
    
    # Single verse reference
    if '.' in ref:
        parts = ref.split('.')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            chapter = int(parts[0])
            verse = int(parts[1])
            return chapter, verse, verse
    
    return None

def extract_john_homilies():
    """Extract homilies and create mappings"""
    
    # Parse the XML
    tree = ET.parse("../texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml")
    root = tree.getroot()
    
    # Find body
    body = root.find('.//ThML.body')
    if body is None:
        body = root.find('.//body')
    
    homilies = []
    verse_to_homilies = {}
    homily_coverage = {}
    
    print("Extracting John homilies...")
    
    # Find all homilies on John (not Hebrews)
    homily_count = 0
    for div in body.findall('.//div2[@type="Homily"]'):
        # Get title from attribute
        title = div.get('title', '')
        
        # Skip if it's Hebrews
        if 'Hebrews' in title:
            continue
            
        # Include Preface and John homilies
        if 'John' not in title and title != 'Preface.':
            continue
            
        homily_count += 1
        
        # Extract verse reference from title
        if title == 'Preface.':
            # Preface is special - it covers John 1:1
            chapter, start_verse, end_verse = 1, 1, 1
        else:
            verse_ref = parse_verse_reference(title)
            
            if verse_ref:
                if len(verse_ref) == 3:
                    chapter, start_verse, end_verse = verse_ref
                else:
                    continue
            else:
                continue
        
        # Create homily info
        homily_info = {
            'number': homily_count,
            'roman': int_to_roman(homily_count),
            'title': title,
            'start_chapter': chapter,
            'start_verse': start_verse,
            'end_chapter': chapter,
            'end_verse': end_verse
        }
        
        homilies.append(homily_info)
        
        # Add to verse mapping
        for verse in range(start_verse, end_verse + 1):
            verse_key = f"{chapter}:{verse}"
            if verse_key not in verse_to_homilies:
                verse_to_homilies[verse_key] = []
            
            verse_to_homilies[verse_key].append({
                'homily_number': homily_count,
                'homily_roman': int_to_roman(homily_count),
                'passage': f"John {chapter}:{start_verse}" if start_verse == end_verse else f"John {chapter}:{start_verse}-{end_verse}",
                'end': f"John {chapter}:{end_verse}"
            })
        
        # Add to coverage
        homily_coverage[str(homily_count)] = {
            'homily_number': homily_count,
            'homily_roman': int_to_roman(homily_count),
            'start_chapter': chapter,
            'start_verse': start_verse,
            'end_chapter': chapter,
            'end_verse': end_verse,
            'title': title
        }
        
        print(f"  Homily {int_to_roman(homily_count)}: {title}")
    
    print(f"\nTotal John homilies found: {homily_count}")
    
    # Save the mappings
    output_dir = "../texts/commentaries/chrysostom/john"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save verse to homilies mapping
    with open(os.path.join(output_dir, "john_verse_to_homilies.json"), "w") as f:
        json.dump(verse_to_homilies, f, indent=2, sort_keys=True)
    
    # Save homily coverage
    with open(os.path.join(output_dir, "homily_coverage.json"), "w") as f:
        json.dump(homily_coverage, f, indent=2)
    
    print(f"\nMappings saved to {output_dir}")
    
    return homilies

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

if __name__ == "__main__":
    extract_john_homilies()
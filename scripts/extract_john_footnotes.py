#!/usr/bin/env python3
"""
Extract footnotes from Chrysostom's John homilies XML and create JSON
"""

import xml.etree.ElementTree as ET
import json
import re
import html

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

def extract_footnotes():
    """Extract footnotes from John homilies"""
    
    # Parse the XML
    tree = ET.parse("../texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml")
    root = tree.getroot()
    
    # Find body
    body = root.find('.//ThML.body')
    if body is None:
        body = root.find('.//body')
    
    print("Extracting footnotes from John homilies...")
    
    footnotes_by_homily = {}
    
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
        roman = int_to_roman(homily_count)
        
        print(f"Processing Homily {roman}: {title}")
        
        # Find all note elements within this homily
        notes = div.findall('.//note')
        
        footnotes = []
        for i, note in enumerate(notes, 1):
            # Get note number from attribute
            note_num = note.get('n', str(i))
            
            # Extract text content
            note_text = ''.join(note.itertext()).strip()
            
            # Clean up the text
            note_text = ' '.join(note_text.split())  # Normalize whitespace
            note_text = html.unescape(note_text)  # Decode HTML entities
            
            if note_text:
                footnotes.append({
                    'original_number': int(note_num) if note_num.isdigit() else i,
                    'display_number': i,  # Sequential numbering within each homily
                    'content': note_text
                })
        
        # Store footnotes for this homily
        footnotes_by_homily[str(homily_count)] = {
            'roman_numeral': roman,
            'footnotes': footnotes
        }
        
        print(f"  Found {len(footnotes)} footnotes")
    
    print(f"\nTotal John homilies processed: {homily_count}")
    
    # Save to JSON
    output_file = "../texts/commentaries/chrysostom/john/footnotes.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(footnotes_by_homily, f, indent=2, ensure_ascii=False)
    
    print(f"Footnotes saved to {output_file}")
    
    # Print summary
    total_footnotes = sum(len(h['footnotes']) for h in footnotes_by_homily.values())
    print(f"\nSummary:")
    print(f"  Total homilies: {len(footnotes_by_homily)}")
    print(f"  Total footnotes: {total_footnotes}")

if __name__ == "__main__":
    extract_footnotes()
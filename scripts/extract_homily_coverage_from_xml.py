#!/usr/bin/env python3
"""
Extract homily coverage (start/end chapters and verses) from Chrysostom's XML file.
Creates a JSON mapping of each homily to its biblical passage coverage.
"""

import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path

def parse_verse_reference(ref_text):
    """
    Parse a verse reference like "Matt. I. 1" or "Matthew 5:17-20"
    Returns: (chapter, start_verse, end_verse)
    """
    # Remove "Matt." or "Matthew" prefix
    ref_text = re.sub(r'^(Matt\.|Matthew)\s*', '', ref_text, flags=re.IGNORECASE)
    
    # Handle Roman numerals for chapters
    roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 
                 'VIII': 8, 'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13,
                 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19,
                 'XX': 20, 'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25,
                 'XXVI': 26, 'XXVII': 27, 'XXVIII': 28}
    
    # Try to match Roman numeral chapter with verse
    roman_match = re.match(r'^([IVX]+)\.\s*(\d+)(?:-(\d+))?', ref_text)
    if roman_match:
        chapter = roman_map.get(roman_match.group(1), 1)
        start_verse = int(roman_match.group(2))
        end_verse = int(roman_match.group(3)) if roman_match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    # Try standard chapter:verse format
    standard_match = re.match(r'^(\d+)[:\.](\d+)(?:-(\d+))?', ref_text)
    if standard_match:
        chapter = int(standard_match.group(1))
        start_verse = int(standard_match.group(2))
        end_verse = int(standard_match.group(3)) if standard_match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    # Try just chapter number
    chapter_match = re.match(r'^(\d+)', ref_text)
    if chapter_match:
        return int(chapter_match.group(1)), 1, 1
    
    # Default
    return 1, 1, 1

def extract_homily_data(xml_path):
    """Extract homily coverage data from the XML file."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Remove namespaces for easier parsing
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    
    homilies = {}
    current_homily = None
    
    # Look for div elements that contain homily titles
    for div in root.iter('div'):
        # Check if this div contains a homily title
        title_elem = div.find('.//head')
        if title_elem is not None and title_elem.text:
            title_text = title_elem.text.strip()
            
            # Match "Homily I." or "Homily 1." patterns
            homily_match = re.match(r'Homily\s+([IVX]+|\d+)\.', title_text, re.IGNORECASE)
            if homily_match:
                # Get homily number
                num_text = homily_match.group(1)
                if num_text.isdigit():
                    homily_num = int(num_text)
                else:
                    # Convert Roman to Arabic
                    roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 
                               'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
                               'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
                               'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
                               'XXI': 21, 'XXII': 22, 'XXIII': 23, 'XXIV': 24, 'XXV': 25,
                               'XXVI': 26, 'XXVII': 27, 'XXVIII': 28, 'XXIX': 29, 'XXX': 30}
                    
                    # Handle compound Roman numerals
                    homily_num = 0
                    remaining = num_text
                    while remaining:
                        found = False
                        for roman, arabic in sorted(roman_map.items(), key=lambda x: -len(x[0])):
                            if remaining.startswith(roman):
                                homily_num += arabic
                                remaining = remaining[len(roman):]
                                found = True
                                break
                        if not found:
                            break
                
                # Look for verse reference in the title or following elements
                verse_ref = None
                
                # Check in the title itself
                ref_match = re.search(r'Matt\.\s*[IVX]+\.\s*\d+|Matthew\s+\d+:\d+', title_text)
                if ref_match:
                    verse_ref = ref_match.group()
                else:
                    # Look in following p elements
                    for p in div.iter('p'):
                        if p.text:
                            ref_match = re.search(r'Matt\.\s*[IVX]+\.\s*\d+|Matthew\s+\d+:\d+', p.text)
                            if ref_match:
                                verse_ref = ref_match.group()
                                break
                
                if verse_ref:
                    chapter, start_verse, end_verse = parse_verse_reference(verse_ref)
                else:
                    # Default values
                    chapter, start_verse, end_verse = 1, 1, 1
                
                # Store homily data
                homilies[homily_num] = {
                    "homily_number": homily_num,
                    "start_chapter": chapter,
                    "start_verse": start_verse,
                    "end_chapter": chapter,  # Will update if we find end reference
                    "end_verse": end_verse
                }
                current_homily = homily_num
    
    # Try to find end references by looking at the next homily's start
    homily_nums = sorted(homilies.keys())
    for i in range(len(homily_nums) - 1):
        current = homily_nums[i]
        next_num = homily_nums[i + 1]
        
        # The end of current homily is typically the verse before the start of next homily
        next_start_ch = homilies[next_num]["start_chapter"]
        next_start_v = homilies[next_num]["start_verse"]
        
        # Set end to verse before next homily starts
        if next_start_v > 1:
            homilies[current]["end_chapter"] = next_start_ch
            homilies[current]["end_verse"] = next_start_v - 1
        else:
            # If next starts at verse 1, end at last verse of previous chapter
            # We'll approximate with verse 50 for now
            homilies[current]["end_chapter"] = next_start_ch - 1 if next_start_ch > 1 else 1
            homilies[current]["end_verse"] = 50
    
    # Last homily - default to chapter 28 (end of Matthew)
    if homily_nums:
        last = homily_nums[-1]
        homilies[last]["end_chapter"] = 28
        homilies[last]["end_verse"] = 20
    
    return homilies

def main():
    xml_path = Path("../texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml")
    output_path = Path("../texts/commentaries/chrysostom/matthew/homily_coverage.json")
    
    if not xml_path.exists():
        print(f"XML file not found: {xml_path}")
        return
    
    print("Extracting homily coverage from XML...")
    homilies = extract_homily_data(xml_path)
    
    # Sort by homily number
    sorted_homilies = dict(sorted(homilies.items()))
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(sorted_homilies, f, indent=2)
    
    print(f"Saved homily coverage to {output_path}")
    print(f"Found {len(homilies)} homilies")
    
    # Print sample
    for num in list(sorted_homilies.keys())[:5]:
        h = sorted_homilies[num]
        print(f"  Homily {num}: Matthew {h['start_chapter']}:{h['start_verse']} - {h['end_chapter']}:{h['end_verse']}")

if __name__ == "__main__":
    main()
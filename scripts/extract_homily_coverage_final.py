#!/usr/bin/env python3
"""
Extract homily coverage from Chrysostom's XML using the structured passage attributes.
"""

import re
import json
from pathlib import Path
import xml.etree.ElementTree as ET

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    result = 0
    prev = 0
    for char in reversed(roman):
        value = values.get(char, 0)
        if value < prev:
            result -= value
        else:
            result += value
        prev = value
    return result

def parse_passage(passage_str):
    """Parse passage like 'Matt. 1:1' or 'Matt. 1:1-16'"""
    # Remove book prefix
    passage_str = re.sub(r'^(Matt\.|Matthew)\s*', '', passage_str, flags=re.IGNORECASE)
    
    # Match patterns like "1:1" or "1:1-16" or "I. 1"
    # Try standard format first
    match = re.match(r'(\d+)[:\.](\d+)(?:[–-](\d+))?', passage_str)
    if match:
        chapter = int(match.group(1))
        start_verse = int(match.group(2))
        end_verse = int(match.group(3)) if match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    # Try Roman numeral format
    match = re.match(r'([IVX]+)\.\s*(\d+)(?:[–-](\d+))?', passage_str)
    if match:
        chapter = roman_to_int(match.group(1))
        start_verse = int(match.group(2))
        end_verse = int(match.group(3)) if match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    return 1, 1, 1

def extract_from_xml_attributes(xml_path):
    """Extract homily coverage using XML structure and attributes."""
    
    # Read file as text first to find div2 elements
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    homilies = {}
    
    # Find all div2 elements with type="Homily"
    # Pattern: <div2 type="Homily" title="Matthew I. 1." n="III"
    div2_pattern = r'<div2[^>]*type="Homily"[^>]*title="([^"]+)"[^>]*n="([IVX]+)"'
    
    for match in re.finditer(div2_pattern, content):
        title = match.group(1)  # e.g., "Matthew I. 1."
        roman_num = match.group(2)  # e.g., "III"
        
        homily_num = roman_to_int(roman_num)
        
        # Parse the passage from title
        chapter, start_verse, end_verse = parse_passage(title)
        
        homilies[homily_num] = {
            "homily_number": homily_num,
            "homily_roman": roman_num,
            "start_chapter": chapter,
            "start_verse": start_verse,
            "end_chapter": chapter,
            "end_verse": end_verse,
            "title": title
        }
    
    # Also look for scripRef elements which might have verse ranges
    # Pattern: <scripRef passage="Matt. 1:1-16"
    scripref_pattern = r'Homily\s+([IVX]+)\..*?<scripRef[^>]*passage="([^"]+)"'
    
    for match in re.finditer(scripref_pattern, content, re.DOTALL):
        roman_num = match.group(1)
        passage = match.group(2)
        
        homily_num = roman_to_int(roman_num)
        
        # Update if we have a range
        if homily_num in homilies and '-' in passage:
            chapter, start_verse, end_verse = parse_passage(passage)
            homilies[homily_num]["end_verse"] = end_verse
    
    # Fill in end chapters/verses based on next homily start
    homily_nums = sorted(homilies.keys())
    
    # Known verse counts per chapter in Matthew
    verse_counts = {
        1: 25, 2: 23, 3: 17, 4: 25, 5: 48, 6: 34, 7: 29, 8: 34,
        9: 38, 10: 42, 11: 30, 12: 50, 13: 58, 14: 36, 15: 39,
        16: 28, 17: 27, 18: 35, 19: 30, 20: 34, 21: 46, 22: 46,
        23: 39, 24: 51, 25: 46, 26: 75, 27: 66, 28: 20
    }
    
    for i in range(len(homily_nums) - 1):
        current = homily_nums[i]
        next_num = homily_nums[i + 1]
        
        current_homily = homilies[current]
        next_homily = homilies[next_num]
        
        # If we don't have an explicit end verse, calculate it
        if current_homily["end_verse"] == current_homily["start_verse"]:
            next_ch = next_homily["start_chapter"]
            next_v = next_homily["start_verse"]
            
            if next_v == 1:
                # Next homily starts new chapter
                end_ch = next_ch - 1 if next_ch > 1 else 1
                end_v = verse_counts.get(end_ch, 50)
            else:
                # Same chapter
                end_ch = next_ch
                end_v = next_v - 1
            
            current_homily["end_chapter"] = end_ch
            current_homily["end_verse"] = end_v
    
    # Last homily goes to end of Matthew
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
    
    print("Extracting homily coverage from XML attributes...")
    homilies = extract_from_xml_attributes(xml_path)
    
    # Save full homily data
    with open(output_path, 'w') as f:
        json.dump(homilies, f, indent=2)
    
    # Create verse-to-homily mapping
    verse_to_homily = {}
    for homily_num, data in homilies.items():
        start_key = f"{data['start_chapter']}:{data['start_verse']}"
        verse_to_homily[start_key] = {
            "homily_number": data["homily_number"],
            "homily_roman": data["homily_roman"],
            "passage": f"Matthew {data['start_chapter']}:{data['start_verse']}",
            "end": f"Matthew {data['end_chapter']}:{data['end_verse']}"
        }
    
    verse_map_path = Path("../texts/commentaries/chrysostom/matthew/matthew_verse_to_homily_clean.json")
    with open(verse_map_path, 'w') as f:
        json.dump(verse_to_homily, f, indent=2)
    
    print(f"Saved homily coverage to {output_path}")
    print(f"Saved verse mapping to {verse_map_path}")
    print(f"Found {len(homilies)} homilies")
    
    # Print all homilies
    print("\nAll homilies:")
    for num in sorted(homilies.keys()):
        h = homilies[num]
        print(f"  Homily {h['homily_roman']:>6} ({num:2d}): Matthew {h['start_chapter']:2d}:{h['start_verse']:2d} - {h['end_chapter']:2d}:{h['end_verse']:2d}  [{h.get('title', 'No title')}]")

if __name__ == "__main__":
    main()
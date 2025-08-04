#!/usr/bin/env python3
"""
Extract ALL homilies from Chrysostom's XML, including Homily I which doesn't have a div2 element.
Look for the pattern "Homily [Roman]." followed by verse reference.
"""

import re
import json
from pathlib import Path

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

def parse_verse_ref(ref_text):
    """Parse verse reference like 'Matt. I. 22, 23.' or 'Matthew 1:1'"""
    # Remove Matt./Matthew prefix
    ref_text = re.sub(r'^(Matt\.|Matthew)\s*', '', ref_text, flags=re.IGNORECASE)
    
    # Handle Roman chapter with verse(s): "I. 22, 23"
    match = re.match(r'([IVX]+)\.\s*(\d+)(?:\s*,\s*(\d+))?', ref_text)
    if match:
        chapter = roman_to_int(match.group(1))
        start_verse = int(match.group(2))
        end_verse = int(match.group(3)) if match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    # Handle standard format: "1:22-23"
    match = re.match(r'(\d+)[:\.](\d+)(?:[–-](\d+))?', ref_text)
    if match:
        chapter = int(match.group(1))
        start_verse = int(match.group(2))
        end_verse = int(match.group(3)) if match.group(3) else start_verse
        return chapter, start_verse, end_verse
    
    return 1, 1, 1

def extract_homilies_comprehensive(xml_path):
    """Extract all homilies by looking for pattern: Homily [Roman]. followed by verse ref"""
    
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    homilies = {}
    
    # Pattern 1: Look for div2 elements with structured data
    div2_pattern = r'<div2[^>]*type="Homily"[^>]*title="([^"]+)"[^>]*n="([IVX]+)"'
    
    for match in re.finditer(div2_pattern, content):
        title = match.group(1)
        roman_num = match.group(2)
        homily_num = roman_to_int(roman_num)
        
        # Special handling for comma-separated verses
        if "22, 23" in title:
            # Homily V starts at verse 22
            chapter, start_verse = 1, 22
            end_verse = 23
        else:
            chapter, start_verse, end_verse = parse_verse_ref(title)
        
        homilies[homily_num] = {
            "homily_number": homily_num,
            "homily_roman": roman_num,
            "start_chapter": chapter,
            "start_verse": start_verse,
            "end_chapter": chapter,
            "end_verse": end_verse,
            "title": title
        }
    
    # Pattern 2: Look for all "Homily [Roman]." patterns followed by verse references
    # This will catch Homily I and any others without div2 elements
    homily_pattern = r'Homily\s+([IVX]+)\.</span></p>\s*\n\s*<p[^>]*>.*?<span[^>]*>Matt\.\s*([^<]+)</span>'
    
    for match in re.finditer(homily_pattern, content, re.DOTALL):
        roman_num = match.group(1)
        verse_ref = match.group(2).strip()
        homily_num = roman_to_int(roman_num)
        
        # Only add if not already found
        if homily_num not in homilies:
            chapter, start_verse, end_verse = parse_verse_ref(verse_ref)
            
            homilies[homily_num] = {
                "homily_number": homily_num,
                "homily_roman": roman_num,
                "start_chapter": chapter,
                "start_verse": start_verse,
                "end_chapter": chapter,
                "end_verse": end_verse,
                "title": f"Matthew {verse_ref}"
            }
    
    # Also check for pattern where verse ref is in a different element
    # Pattern: "Homily V." ... "Matt. I. 22, 23"
    alt_pattern = r'<span[^>]*>Homily\s+([IVX]+)\.</span>.*?<span[^>]*>Matt\.\s*([^<]+)</span>'
    
    for match in re.finditer(alt_pattern, content, re.DOTALL):
        roman_num = match.group(1)
        verse_ref = match.group(2).strip()
        homily_num = roman_to_int(roman_num)
        
        # Skip if too far apart (more than 500 chars)
        if len(match.group(0)) > 500:
            continue
            
        # Only add if not already found
        if homily_num not in homilies:
            chapter, start_verse, end_verse = parse_verse_ref(verse_ref)
            
            homilies[homily_num] = {
                "homily_number": homily_num,
                "homily_roman": roman_num,
                "start_chapter": chapter,
                "start_verse": start_verse,
                "end_chapter": chapter,
                "end_verse": end_verse,
                "title": f"Matthew {verse_ref}"
            }
    
    # Manually add Homily I if still missing (it's an introduction, may not have specific verses)
    if 1 not in homilies:
        homilies[1] = {
            "homily_number": 1,
            "homily_roman": "I",
            "start_chapter": 1,
            "start_verse": 1,
            "end_chapter": 1,
            "end_verse": 1,
            "title": "Introduction"
        }
    
    # Calculate end verses based on next homily
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
        if homilies[last]["end_verse"] == homilies[last]["start_verse"]:
            homilies[last]["end_chapter"] = 28
            homilies[last]["end_verse"] = 20
    
    return homilies

def main():
    xml_path = Path("../texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml")
    output_path = Path("../texts/commentaries/chrysostom/matthew/homily_coverage_complete.json")
    
    if not xml_path.exists():
        print(f"XML file not found: {xml_path}")
        return
    
    print("Extracting ALL homilies from XML...")
    homilies = extract_homilies_comprehensive(xml_path)
    
    # Save full homily data
    with open(output_path, 'w') as f:
        json.dump(homilies, f, indent=2)
    
    print(f"Saved homily coverage to {output_path}")
    print(f"Found {len(homilies)} homilies")
    
    # Print all homilies
    print("\nAll homilies:")
    for num in sorted(homilies.keys()):
        h = homilies[num]
        print(f"  Homily {h['homily_roman']:>6} ({num:2d}): Matthew {h['start_chapter']:2d}:{h['start_verse']:2d} - {h['end_chapter']:2d}:{h['end_verse']:2d}  [{h.get('title', 'No title')}]")

if __name__ == "__main__":
    main()
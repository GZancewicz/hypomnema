#!/usr/bin/env python3
"""
Extract homily coverage (start/end chapters and verses) from Chrysostom's XML file.
Creates a JSON mapping of each homily to its biblical passage coverage.
"""

import re
import json
from pathlib import Path

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    roman_map = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100
    }
    
    result = 0
    prev = 0
    
    for char in reversed(roman):
        value = roman_map.get(char, 0)
        if value < prev:
            result -= value
        else:
            result += value
        prev = value
    
    return result

def parse_verse_reference(text, context_lines=None):
    """
    Parse a verse reference from text.
    Returns: (chapter, start_verse, end_verse)
    """
    # Look for patterns like "Matt. I. 1" or "Matthew 5:17"
    patterns = [
        # Matt. I. 1 format
        r'Matt\.\s+([IVX]+)\.\s+(\d+)(?:[–-](\d+))?',
        # Matthew 1:1 format
        r'Matthew\s+(\d+)[:\.](\d+)(?:[–-](\d+))?',
        # Chapter I. verse format
        r'Chapter\s+([IVX]+)\.\s+(?:verse\s+)?(\d+)(?:[–-](\d+))?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Get chapter
            chapter_str = match.group(1)
            if chapter_str.isdigit():
                chapter = int(chapter_str)
            else:
                chapter = roman_to_int(chapter_str)
            
            # Get verses
            start_verse = int(match.group(2))
            end_verse = int(match.group(3)) if match.group(3) else start_verse
            
            return chapter, start_verse, end_verse
    
    # If no match found, return defaults
    return 1, 1, 1

def extract_homilies_from_xml(xml_path):
    """Extract homily data by parsing XML content line by line."""
    
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    homilies = {}
    
    # Find all homily titles
    homily_pattern = r'<span[^>]*>Homily\s+([IVX]+)\.</span>'
    
    for match in re.finditer(homily_pattern, content):
        roman_num = match.group(1)
        homily_num = roman_to_int(roman_num)
        
        # Get position in content
        start_pos = match.end()
        
        # Find the next homily or end of content
        next_homily = re.search(homily_pattern, content[start_pos:])
        if next_homily:
            end_pos = start_pos + next_homily.start()
        else:
            end_pos = len(content)
        
        # Extract section between this homily and next
        homily_content = content[start_pos:end_pos]
        
        # Look for verse reference in the first 1000 characters
        search_text = homily_content[:1000]
        chapter, start_verse, end_verse = parse_verse_reference(search_text)
        
        # Store homily data
        homilies[homily_num] = {
            "homily_number": homily_num,
            "homily_roman": roman_num,
            "start_chapter": chapter,
            "start_verse": start_verse,
            "end_chapter": chapter,
            "end_verse": end_verse
        }
    
    # Now try to infer end points based on next homily's start
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
        
        next_ch = homilies[next_num]["start_chapter"]
        next_v = homilies[next_num]["start_verse"]
        
        # If next homily starts at verse 1, end current at last verse of previous chapter
        if next_v == 1:
            end_ch = next_ch - 1 if next_ch > 1 else 1
            end_v = verse_counts.get(end_ch, 50)
        else:
            # End at verse before next homily
            end_ch = next_ch
            end_v = next_v - 1
        
        homilies[current]["end_chapter"] = end_ch
        homilies[current]["end_verse"] = end_v
    
    # Handle last homily - goes to end of Matthew
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
    homilies = extract_homilies_from_xml(xml_path)
    
    # Convert to format: "chapter:verse" -> homily data
    verse_to_homily = {}
    
    for homily_num, data in homilies.items():
        # Add starting verse
        start_key = f"{data['start_chapter']}:{data['start_verse']}"
        verse_to_homily[start_key] = {
            "homily_number": data["homily_number"],
            "homily_roman": data["homily_roman"],
            "passage": f"Matthew {data['start_chapter']}:{data['start_verse']}",
            "end": f"Matthew {data['end_chapter']}:{data['end_verse']}"
        }
    
    # Save both formats
    with open(output_path, 'w') as f:
        json.dump(homilies, f, indent=2)
    
    verse_map_path = Path("../texts/commentaries/chrysostom/matthew/verse_to_homily_clean.json")
    with open(verse_map_path, 'w') as f:
        json.dump(verse_to_homily, f, indent=2)
    
    print(f"Saved homily coverage to {output_path}")
    print(f"Saved verse mapping to {verse_map_path}")
    print(f"Found {len(homilies)} homilies")
    
    # Print sample
    for num in list(sorted(homilies.keys()))[:10]:
        h = homilies[num]
        print(f"  Homily {num}: Matthew {h['start_chapter']}:{h['start_verse']} - {h['end_chapter']}:{h['end_verse']}")

if __name__ == "__main__":
    main()
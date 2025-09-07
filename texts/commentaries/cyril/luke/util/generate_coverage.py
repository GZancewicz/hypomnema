#!/usr/bin/env python3
"""
Generate coverage.json and verse_mapping.json for Cyril Luke sermons.
Shows which verses each sermon covers.
"""

import os
import json
import re
from pathlib import Path

def extract_verse_from_subtitle(subtitle):
    """Extract verse range from subtitle like 'Luke 2:8-18' or '2:8-18'"""
    # Try to match patterns like "2:8-18", "Luke 2:8-18", etc.
    patterns = [
        r'(?:Luke\s+)?(\d+):(\d+)-(\d+):(\d+)',  # 2:8-3:5
        r'(?:Luke\s+)?(\d+):(\d+)-(\d+)',         # 2:8-18
        r'(?:Luke\s+)?(\d+):(\d+)',               # 2:8
        r'Luke\s+(\d+)',                          # Luke 12
        r'^(\d+)$',                               # Just chapter number
    ]
    
    for pattern in patterns:
        match = re.search(pattern, subtitle)
        if match:
            groups = match.groups()
            if len(groups) == 4:  # chapter:verse-chapter:verse
                return {
                    "start": {"chapter": int(groups[0]), "verse": int(groups[1])},
                    "end": {"chapter": int(groups[2]), "verse": int(groups[3])}
                }
            elif len(groups) == 3:  # chapter:verse-verse
                return {
                    "start": {"chapter": int(groups[0]), "verse": int(groups[1])},
                    "end": {"chapter": int(groups[0]), "verse": int(groups[2])}
                }
            elif len(groups) == 2:  # chapter:verse
                return {
                    "start": {"chapter": int(groups[0]), "verse": int(groups[1])},
                    "end": {"chapter": int(groups[0]), "verse": int(groups[1])}
                }
            elif len(groups) == 1:  # chapter only
                return {
                    "start": {"chapter": int(groups[0]), "verse": 1},
                    "end": {"chapter": int(groups[0]), "verse": 99}
                }
    
    # Default if no pattern matches
    return {
        "start": {"chapter": 1, "verse": 1},
        "end": {"chapter": 1, "verse": 1}
    }

def generate_coverage():
    """Generate coverage data from content files."""
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    coverage = {
        'commentary': 'cyril_luke',
        'total_homilies': 0,  # Will be updated
        'homilies': []
    }
    
    # Also prepare verse mapping
    verse_mapping = {}
    
    # Scan all existing directories
    sermon_dirs = sorted([d for d in content_dir.iterdir() if d.is_dir()])
    
    for sermon_dir in sermon_dirs:
        sermon_num = int(sermon_dir.name)
        content_file = sermon_dir / 'content.json'
        
        if not content_file.exists():
            print(f"Warning: No content.json for sermon {sermon_num}")
            continue
        
        with open(content_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        # Extract Roman numeral from title
        title = content.get('title', f'Sermon {sermon_num}')
        roman_match = re.search(r'Sermon\s+([IVXLC]+)', title)
        if roman_match:
            roman = roman_match.group(1)
        else:
            roman = str(sermon_num)
        
        # Extract scripture reference from subtitle
        subtitle = content.get('subtitle', '')
        scripture_ref = extract_verse_from_subtitle(subtitle)
        
        sermon_coverage = {
            'id': sermon_num,
            'roman': roman,
            'title': title,
            'start': scripture_ref['start'],
            'end': scripture_ref['end']
        }
        
        coverage['homilies'].append(sermon_coverage)
        
        # Add to verse mapping
        start_ch = scripture_ref['start']['chapter']
        end_ch = scripture_ref['end']['chapter']
        
        for chapter in range(start_ch, end_ch + 1):
            ch_str = str(chapter)
            if ch_str not in verse_mapping:
                verse_mapping[ch_str] = []
            
            # Don't add duplicates
            if sermon_num not in [h["id"] for h in verse_mapping[ch_str]]:
                verse_mapping[ch_str].append({
                    "id": sermon_num,
                    "roman": roman
                })
    
    # Update total count
    coverage['total_homilies'] = len(coverage['homilies'])
    
    # Save coverage.json
    coverage_file = base_dir / 'coverage.json'
    with open(coverage_file, 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    
    # Save verse_mapping.json
    mapping_file = base_dir / 'verse_mapping.json'
    # Sort chapters and homilies within each chapter
    sorted_mapping = {}
    for chapter in sorted(verse_mapping.keys(), key=int):
        sorted_mapping[chapter] = sorted(verse_mapping[chapter], key=lambda x: x["id"])
    
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_mapping, f, indent=2, ensure_ascii=False)
    
    print(f"Coverage generated for {len(coverage['homilies'])} sermons")
    print(f"Created {coverage_file}")
    print(f"Created {mapping_file}")
    return coverage

def get_chapter_verse_count(chapter):
    """Get verse count for a Luke chapter."""
    # Luke chapter verse counts
    verse_counts = {
        1: 25, 2: 23, 3: 17, 4: 25, 5: 48, 6: 34, 7: 29, 8: 34,
        9: 38, 10: 42, 11: 30, 12: 50, 13: 58, 14: 36, 15: 39, 16: 28,
        17: 27, 18: 35, 19: 30, 20: 34, 21: 46, 22: 46, 23: 39, 24: 51,
        25: 46, 26: 75, 27: 66, 28: 20
    }
    return verse_counts.get(chapter, 30)  # Default to 30 if not found

def main():
    print("Generating coverage for Cyril Luke...")
    print("-" * 50)
    generate_coverage()

if __name__ == "__main__":
    main()
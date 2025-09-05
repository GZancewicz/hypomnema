#!/usr/bin/env python3
"""
Generate coverage.json for Cyril Luke sermons.
Shows which verses each sermon covers.
"""

import os
import json
from pathlib import Path

def generate_coverage():
    """Generate coverage data from metadata files."""
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    coverage = {
        'commentary': 'cyril_luke',
        'total_sermons': 153,
        'sermons': []
    }
    
    for sermon_num in range(1, 154):
        sermon_dir = content_dir / f'{sermon_num:03d}'
        metadata_file = sermon_dir / 'metadata.json'
        
        if not metadata_file.exists():
            print(f"Warning: No metadata for sermon {sermon_num}")
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        scripture_ref = metadata.get('scripture_reference', {})
        
        sermon_coverage = {
            'id': sermon_num,
            'roman': metadata.get('roman', ''),
            'title': metadata.get('title', ''),
            'start': scripture_ref.get('start', {'chapter': 1, 'verse': 1}),
            'end': scripture_ref.get('end', {'chapter': 1, 'verse': 1}),
            'verses_covered': []
        }
        
        # Calculate verses covered
        start_ch = sermon_coverage['start']['chapter']
        start_v = sermon_coverage['start']['verse']
        end_ch = sermon_coverage['end']['chapter']
        end_v = sermon_coverage['end']['verse']
        
        if start_ch == end_ch:
            # Same chapter
            for v in range(start_v, end_v + 1):
                sermon_coverage['verses_covered'].append(f"{start_ch}:{v}")
        else:
            # Multiple chapters
            # First chapter
            for v in range(start_v, get_chapter_verse_count(start_ch) + 1):
                sermon_coverage['verses_covered'].append(f"{start_ch}:{v}")
            
            # Middle chapters
            for ch in range(start_ch + 1, end_ch):
                for v in range(1, get_chapter_verse_count(ch) + 1):
                    sermon_coverage['verses_covered'].append(f"{ch}:{v}")
            
            # Last chapter
            for v in range(1, end_v + 1):
                sermon_coverage['verses_covered'].append(f"{end_ch}:{v}")
        
        coverage['sermons'].append(sermon_coverage)
    
    # Save coverage.json
    coverage_file = base_dir / 'coverage.json'
    with open(coverage_file, 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    
    print(f"Coverage generated for {len(coverage['sermons'])} sermons")
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
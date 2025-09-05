#!/usr/bin/env python3
"""
Generate verse_mapping.json for Chrysostom Matthew commentary.
Maps individual verses to homilies that comment on them.
"""

import os
import sys
import json
from pathlib import Path

def generate_verse_mapping():
    """Generate verse-to-homily mapping for Matthew."""
    base_dir = Path(__file__).parent.parent
    coverage_file = base_dir / 'coverage.json'
    
    if not coverage_file.exists():
        print("Error: coverage.json not found. Run generate_coverage.py first.")
        return
    
    with open(coverage_file, 'r', encoding='utf-8') as f:
        coverage = json.load(f)
    
    verse_map = {}
    
    for homily in coverage['homilies']:
        homily_id = homily['id']
        start_ch = homily['start']['chapter']
        start_v = homily['start']['verse']
        end_ch = homily['end']['chapter']
        end_v = homily['end']['verse']
        
        # Add verses covered
        if start_ch == end_ch:
            for v in range(start_v, end_v + 1):
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
        else:
            # Handle multi-chapter ranges
            for v in range(start_v, 100):  # First chapter
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
            
            # Middle chapters
            for ch in range(start_ch + 1, end_ch):
                for v in range(1, 100):
                    verse_ref = f"{ch}:{v}"
                    if verse_ref not in verse_map:
                        verse_map[verse_ref] = []
                    verse_map[verse_ref].append({
                        'id': homily_id,
                        'roman': homily['roman'],
                        'type': 'primary'
                    })
            
            # Last chapter
            for v in range(1, end_v + 1):
                verse_ref = f"{end_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
    
    # Save verse_mapping.json
    with open(base_dir / 'verse_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2, ensure_ascii=False)
    
    print(f"Generated mapping for {len(verse_map)} verse references")

def main():
    print("Generating Chrysostom Matthew Verse Mapping")
    print("=" * 60)
    generate_verse_mapping()
    print("\nVerse mapping generation complete!")

if __name__ == "__main__":
    main()
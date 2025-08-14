#!/usr/bin/env python3
"""
Generate verse_mapping.json for Chrysostom John homilies.
Maps each verse to the homilies that comment on it.
"""

import os
import json
from pathlib import Path

def generate_verse_mapping():
    """Generate verse to homily mapping."""
    base_dir = Path(__file__).parent.parent
    
    # First load coverage data
    coverage_file = base_dir / 'coverage.json'
    if not coverage_file.exists():
        print("Coverage file not found. Run generate_coverage.py first.")
        return
    
    with open(coverage_file, 'r', encoding='utf-8') as f:
        coverage = json.load(f)
    
    # Build verse to homily mapping
    verse_map = {}
    
    for homily in coverage['homilies']:
        homily_id = homily['id']
        homily_roman = homily['roman']
        
        for verse_ref in homily.get('verses_covered', []):
            if verse_ref not in verse_map:
                verse_map[verse_ref] = []
            
            verse_map[verse_ref].append({
                'id': homily_id,
                'roman': homily_roman,
                'type': 'primary'  # Primary coverage
            })
    
    # Add secondary references from scripture_references.json files
    content_dir = base_dir / 'content'
    
    for homily_num in range(1, 89):
        homily_dir = content_dir / f'{homily_num:03d}'
        ref_file = homily_dir / 'scripture_references.json'
        
        if not ref_file.exists():
            continue
        
        with open(ref_file, 'r', encoding='utf-8') as f:
            references = json.load(f)
        
        # Get homily roman numeral
        metadata_file = homily_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            roman = metadata.get('roman', '')
        else:
            roman = to_roman(homily_num)
        
        # Add John references as secondary
        for ref in references.get('john', []):
            verse_ref = f"{ref['chapter']}:{ref['verse']}"
            
            if verse_ref not in verse_map:
                verse_map[verse_ref] = []
            
            # Check if this homily already has primary coverage
            already_primary = any(
                h['id'] == homily_num and h['type'] == 'primary' 
                for h in verse_map[verse_ref]
            )
            
            if not already_primary:
                # Add as secondary reference
                existing = [h for h in verse_map[verse_ref] if h['id'] == homily_num]
                if not existing:
                    verse_map[verse_ref].append({
                        'id': homily_num,
                        'roman': roman,
                        'type': 'reference'  # Secondary reference
                    })
    
    # Sort verse map by chapter and verse
    sorted_map = {}
    for verse_ref in sorted(verse_map.keys(), key=lambda x: parse_verse_ref(x)):
        sorted_map[verse_ref] = sorted(verse_map[verse_ref], key=lambda x: x['id'])
    
    # Save verse_mapping.json
    mapping_file = base_dir / 'verse_mapping.json'
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_map, f, indent=2, ensure_ascii=False)
    
    print(f"Verse mapping generated for {len(sorted_map)} verses")
    return sorted_map

def parse_verse_ref(ref):
    """Parse verse reference for sorting."""
    parts = ref.split(':')
    if len(parts) == 2:
        return (int(parts[0]), int(parts[1]))
    return (0, 0)

def to_roman(num):
    """Convert number to Roman numeral."""
    values = [
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    result = ''
    for value, letter in values:
        count = num // value
        if count:
            result += letter * count
            num -= value * count
    return result

def main():
    print("Generating verse mapping for Chrysostom John...")
    print("-" * 50)
    generate_verse_mapping()

if __name__ == "__main__":
    main()
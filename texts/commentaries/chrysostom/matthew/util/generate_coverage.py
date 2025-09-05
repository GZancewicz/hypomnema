#!/usr/bin/env python3
"""
Generate coverage.json for Chrysostom Matthew commentary.
Maps homilies to scripture passages they cover.
"""

import os
import sys
import json
from pathlib import Path

def generate_coverage():
    """Generate coverage map for all Matthew homilies."""
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    coverage = {
        'commentary': 'chrysostom_matthew',
        'total_homilies': 90,
        'homilies': []
    }
    
    for homily_num in range(1, 91):
        metadata_file = content_dir / f'{homily_num:03d}' / 'metadata.json'
        
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        scripture_ref = metadata.get('scripture_reference')
        if scripture_ref:
            coverage['homilies'].append({
                'id': homily_num,
                'roman': metadata['roman'],
                'title': metadata['title'],
                'start': scripture_ref.get('start', {'chapter': 1, 'verse': 1}),
                'end': scripture_ref.get('end', {'chapter': 1, 'verse': 1})
            })
    
    # Save coverage.json
    with open(base_dir / 'coverage.json', 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    
    print(f"Generated coverage for {len(coverage['homilies'])} homilies")

def main():
    print("Generating Chrysostom Matthew Coverage")
    print("=" * 60)
    generate_coverage()
    print("\nCoverage generation complete!")

if __name__ == "__main__":
    main()
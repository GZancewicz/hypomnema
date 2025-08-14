#!/usr/bin/env python3
"""
Generate complete coverage.json and verse_mapping.json for all 88 John homilies.
"""

import json
from pathlib import Path

def extract_chapter_verse(display):
    """Extract chapter and verse from display string."""
    import re
    
    if not display:
        return None, None
    
    # Match patterns like "John 5:31" or "John 5:31-33"
    match = re.search(r'John\s+(\d+)[:\.](\d+)(?:-(\d+))?', display)
    if match:
        chapter = int(match.group(1))
        verse = int(match.group(2))
        end_verse = int(match.group(3)) if match.group(3) else verse
        return chapter, verse, end_verse
    
    return None, None, None

def generate_coverage_and_mapping():
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    # Generate coverage.json
    print("Generating complete coverage.json...")
    coverage = {
        'commentary': 'chrysostom_john',
        'total_homilies': 88,
        'homilies': []
    }
    
    for homily_num in range(1, 89):
        metadata_file = content_dir / f'{homily_num:03d}' / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            scripture_ref = metadata.get('scripture_reference', {})
            
            # Extract chapter and verse from display or subtitle
            chapter = verse = end_verse = None
            
            if scripture_ref and scripture_ref.get('display'):
                chapter, verse, end_verse = extract_chapter_verse(scripture_ref.get('display'))
            elif metadata.get('subtitle'):
                chapter, verse, end_verse = extract_chapter_verse(metadata.get('subtitle'))
            
            # Add to coverage if we have valid reference
            if chapter and verse:
                coverage['homilies'].append({
                    'id': homily_num,
                    'roman': metadata.get('roman', f'{homily_num}'),
                    'title': metadata.get('title', f'Homily {homily_num}'),
                    'start': {'chapter': chapter, 'verse': verse},
                    'end': {'chapter': chapter, 'verse': end_verse or verse}
                })
            else:
                print(f"  Homily {homily_num}: No scripture reference found")
    
    with open(base_dir / 'coverage.json', 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    
    print(f"Generated coverage with {len(coverage['homilies'])} homilies")
    
    # Generate verse_mapping.json
    print("\nGenerating verse_mapping.json...")
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
    
    with open(base_dir / 'verse_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2, ensure_ascii=False)
    
    print(f"Generated verse mapping with {len(verse_map)} verse references")
    
    print("\nAll JSON files generated successfully!")

def main():
    print("Complete John Coverage and Verse Mapping Generation")
    print("=" * 60)
    generate_coverage_and_mapping()

if __name__ == "__main__":
    main()
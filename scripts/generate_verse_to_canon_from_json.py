#!/usr/bin/env python3
"""Generate verse-to-canon mapping from existing JSON files"""

import json
import re
from pathlib import Path

def parse_section_reference(ref_str):
    """Parse a section reference like '3.3' or '1.23' to get chapter and verse"""
    match = re.match(r'(\d+)\.(\d+)', ref_str)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

def parse_verse_range(ref_str):
    """Parse verse reference like '1:1-16' or '3:3' to get starting verse"""
    ref_str = ref_str.strip()
    if '-' in ref_str:
        start = ref_str.split('-')[0].strip()
    else:
        start = ref_str

    if ':' in start:
        parts = start.split(':')
        chapter = int(parts[0])
        verse_str = re.sub(r'[A-Z]+$', '', parts[1])
        try:
            verse = int(verse_str)
            return chapter, verse
        except ValueError:
            return None, None
    return None, None

def main():
    print("Building verse-to-canon mapping from JSON files...")

    base_path = Path('texts/reference/eusebian_canons')

    # Load canon lookup
    with open(base_path / 'canon_lookup.json', 'r') as f:
        canon_lookup = json.load(f)

    # Load section files for each gospel
    gospels = {
        'matthew': 'Matthew',
        'mark': 'Mark',
        'luke': 'Luke',
        'john': 'John'
    }

    section_data = {}
    for gospel_lower, gospel_title in gospels.items():
        section_file = base_path / 'data' / f'{gospel_lower}_sections.json'
        with open(section_file, 'r') as f:
            sections = json.load(f)
            section_data[gospel_lower] = {s['section']: s['reference'] for s in sections}

    # Build verse-to-canon mapping
    verse_mapping = {
        'matthew': {},
        'mark': {},
        'luke': {},
        'john': {}
    }

    # Process each canon entry
    for canon_key, gospel_sections in canon_lookup.items():
        for gospel_title, section_ref in gospel_sections.items():
            gospel_lower = gospel_title.lower()

            # Parse section number from reference like "8 - 3.3"
            section_match = re.match(r'(\d+)\s*-', section_ref)
            if not section_match:
                continue

            section_num = int(section_match.group(1))

            # Get the verse reference for this section
            if section_num not in section_data[gospel_lower]:
                continue

            verse_ref = section_data[gospel_lower][section_num]

            # Parse the starting verse
            chapter, verse = parse_verse_range(verse_ref)
            if chapter and verse:
                verse_key = f"{chapter}:{verse}"
                verse_mapping[gospel_lower][verse_key] = canon_key

    # Save to JSON
    output_file = base_path / 'verse_to_canon.json'
    with open(output_file, 'w') as f:
        json.dump(verse_mapping, f, indent=2, sort_keys=True)

    print(f"✓ Saved verse mappings to {output_file}")

    # Show statistics
    for gospel in ['matthew', 'mark', 'luke', 'john']:
        count = len(verse_mapping[gospel])
        print(f"  {gospel.capitalize()}: {count} verses with canon references")

    # Show sample
    print("\nSample mappings:")
    print(f"  Matthew 3:3 -> {verse_mapping['matthew'].get('3:3', 'Not found')}")
    print(f"  Mark 1:3 -> {verse_mapping['mark'].get('1:3', 'Not found')}")
    print(f"  Luke 3:3 -> {verse_mapping['luke'].get('3:3', 'Not found')}")
    print(f"  John 1:23 -> {verse_mapping['john'].get('1:23', 'Not found')}")

if __name__ == "__main__":
    main()

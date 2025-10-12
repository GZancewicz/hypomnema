#!/usr/bin/env python3
"""
Generate complete canon lookup for every verse in the Gospels.
Each verse gets mapped to its canon (I-X) and section number.
"""

import json
import re
from pathlib import Path
from collections import OrderedDict

def parse_verse_range(ref_str):
    """Parse verse reference like '1.1-16' or '3.3' to get chapter and verse range"""
    ref_str = ref_str.strip()

    # Handle range like "1.1-16"
    if '-' in ref_str:
        start_part, end_part = ref_str.split('-')
        start_chapter, start_verse = map(int, start_part.split('.'))

        # End might be just a verse number or chapter.verse
        if '.' in end_part:
            end_chapter, end_verse = map(int, end_part.split('.'))
        else:
            end_chapter = start_chapter
            end_verse = int(end_part)
    else:
        # Single verse like "3.3"
        start_chapter, start_verse = map(int, ref_str.split('.'))
        end_chapter, end_verse = start_chapter, start_verse

    return start_chapter, start_verse, end_chapter, end_verse

def generate_verse_list(start_ch, start_v, end_ch, end_v, max_verses_per_chapter):
    """Generate list of all verses in a range"""
    verses = []

    if start_ch == end_ch:
        # Same chapter
        for v in range(start_v, end_v + 1):
            verses.append(f"{start_ch}:{v}")
    else:
        # Multiple chapters
        # First chapter: start_v to end of chapter
        for v in range(start_v, max_verses_per_chapter.get(start_ch, 99) + 1):
            verses.append(f"{start_ch}:{v}")

        # Middle chapters: all verses
        for ch in range(start_ch + 1, end_ch):
            for v in range(1, max_verses_per_chapter.get(ch, 99) + 1):
                verses.append(f"{ch}:{v}")

        # Last chapter: 1 to end_v
        for v in range(1, end_v + 1):
            verses.append(f"{end_ch}:{v}")

    return verses

def main():
    print("Generating complete canon lookup for all Gospel verses...")

    base_path = Path(__file__).parent.parent

    # Load canon lookup (format: "III.3" -> {gospel: "section - verse_range"})
    with open(base_path / 'canon_lookup.json', 'r') as f:
        canon_lookup = json.load(f)

    # Load section files for each gospel
    gospels = ['matthew', 'mark', 'luke', 'john']
    section_data = {}

    for gospel in gospels:
        section_file = base_path / 'data' / f'{gospel}_sections.json'
        with open(section_file, 'r') as f:
            sections = json.load(f)
            section_data[gospel] = {s['section']: s['reference'] for s in sections}

    # Rough max verses per chapter (generous estimates)
    max_verses = {
        'matthew': {1: 25, 2: 23, 3: 17, 4: 25, 5: 48, 6: 34, 7: 29, 8: 34, 9: 38, 10: 42,
                   11: 30, 12: 50, 13: 58, 14: 36, 15: 39, 16: 28, 17: 27, 18: 35, 19: 30, 20: 34,
                   21: 46, 22: 46, 23: 39, 24: 51, 25: 46, 26: 75, 27: 66, 28: 20},
        'mark': {1: 45, 2: 28, 3: 35, 4: 41, 5: 43, 6: 56, 7: 37, 8: 38, 9: 50, 10: 52,
                11: 33, 12: 44, 13: 37, 14: 72, 15: 47, 16: 20},
        'luke': {1: 80, 2: 52, 3: 38, 4: 44, 5: 39, 6: 49, 7: 50, 8: 56, 9: 62, 10: 42,
                11: 54, 12: 59, 13: 35, 14: 35, 15: 32, 16: 31, 17: 37, 18: 43, 19: 48, 20: 47,
                21: 38, 22: 71, 23: 56, 24: 53},
        'john': {1: 51, 2: 25, 3: 36, 4: 54, 5: 47, 6: 71, 7: 53, 8: 59, 9: 41, 10: 42,
                11: 57, 12: 50, 13: 38, 14: 31, 15: 27, 16: 33, 17: 26, 18: 40, 19: 42, 20: 31, 21: 25}
    }

    # Build complete mapping
    full_lookup = {
        'matthew': OrderedDict(),
        'mark': OrderedDict(),
        'luke': OrderedDict(),
        'john': OrderedDict()
    }

    # Process each canon entry
    for canon_key, gospel_sections in canon_lookup.items():
        # Parse canon key like "III.3" into canon="III" and section=3
        canon_match = re.match(r'([IVX]+)\.(\d+)', canon_key)
        if not canon_match:
            continue

        canon_num = canon_match.group(1)
        section_num = int(canon_match.group(2))

        # Process each gospel in this canon
        for gospel_title, section_ref in gospel_sections.items():
            gospel_lower = gospel_title.lower()

            # Parse section number from reference like "8 - 3.3-10"
            section_match = re.match(r'(\d+)\s*-\s*(.+)', section_ref)
            if not section_match:
                continue

            verse_range = section_match.group(2)

            try:
                # Parse the verse range
                start_ch, start_v, end_ch, end_v = parse_verse_range(verse_range)

                # Generate all verses in this range
                verses = generate_verse_list(start_ch, start_v, end_ch, end_v,
                                            max_verses.get(gospel_lower, {}))

                # Assign canon and section to each verse
                for verse_key in verses:
                    full_lookup[gospel_lower][verse_key] = {
                        'canon': canon_num,
                        'section': section_num
                    }

            except Exception as e:
                print(f"Warning: Could not parse {gospel_title} {verse_range}: {e}")
                continue

    output_file = base_path / 'canon_lookup_full.json'

    final_output = {}
    for gospel in gospels:
        verses_list = []
        for verse_key, data in full_lookup[gospel].items():
            chapter, verse = map(int, verse_key.split(':'))
            verses_list.append((chapter, verse, data))

        verses_list.sort(key=lambda x: (x[0], x[1]))

        sorted_dict = {}
        for chapter, verse, data in verses_list:
            verse_key = f"{chapter}:{verse}"
            sorted_dict[verse_key] = data

        final_output[gospel] = sorted_dict

    with open(output_file, 'w') as f:
        f.write('{\n')
        for gi, gospel in enumerate(gospels):
            f.write(f'  "{gospel}": {{\n')
            verses = [(int(k.split(':')[0]), int(k.split(':')[1]), k, v)
                     for k, v in final_output[gospel].items()]
            verses.sort(key=lambda x: (x[0], x[1]))

            for i, (ch, v, verse_key, data) in enumerate(verses):
                comma = ',' if i < len(verses) - 1 else ''
                canon = data['canon']
                section = data['section']
                f.write(f'    "{verse_key}": {{"canon": "{canon}", "section": {section}}}{comma}\n')

            gospel_comma = ',' if gi < len(gospels) - 1 else ''
            f.write(f'  }}{gospel_comma}\n')
        f.write('}\n')

    print(f"✓ Saved complete canon lookup to {output_file}")

    for gospel in gospels:
        count = len(final_output[gospel])
        print(f"  {gospel.capitalize()}: {count} verses")

    print("\nSample mappings:")
    for gospel in gospels:
        first_keys = list(final_output[gospel].keys())[:3]
        if first_keys:
            samples = [f"{k}→{final_output[gospel][k]['canon']}.{final_output[gospel][k]['section']}"
                      for k in first_keys]
            print(f"  {gospel.capitalize()}: {', '.join(samples)}")

    print("\nTest case:")
    if '1:17' in final_output['matthew']:
        result = final_output['matthew']['1:17']
        print(f"  Matthew 1:17 → Canon {result['canon']}, Section {result['section']}")
    else:
        print("  Matthew 1:17 → NOT FOUND")

if __name__ == "__main__":
    main()

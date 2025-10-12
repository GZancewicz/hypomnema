#!/usr/bin/env python3
import json
from pathlib import Path

def parse_verse_range(reference):
    import re

    def clean_verse(v_str):
        return int(re.sub(r'[A-Z]+', '', v_str))

    verses = []
    if '-' in reference:
        start, end = reference.split('-')
        start_parts = start.split(':')
        start_ch = int(start_parts[0])
        start_v = clean_verse(start_parts[1])

        if ':' in end:
            end_parts = end.split(':')
            end_ch = int(end_parts[0])
            end_v = clean_verse(end_parts[1])
        else:
            end_ch = start_ch
            end_v = clean_verse(end)

        if start_ch == end_ch:
            for v in range(start_v, end_v + 1):
                verses.append((start_ch, v))
        else:
            for v in range(start_v, 200):
                verses.append((start_ch, v))
            for ch in range(start_ch + 1, end_ch):
                for v in range(1, 200):
                    verses.append((ch, v))
            for v in range(1, end_v + 1):
                verses.append((end_ch, v))
    else:
        parts = reference.split(':')
        ch = int(parts[0])
        v = clean_verse(parts[1])
        verses.append((ch, v))

    return verses

def main():
    base_path = Path(__file__).parent.parent

    with open(base_path / 'harmony.json') as f:
        harmony = json.load(f)

    section_data = {}
    for gospel in ['matthew', 'mark', 'luke', 'john']:
        with open(base_path / 'data' / f'{gospel}_sections.json') as f:
            sections = json.load(f)
            section_data[gospel] = {s['section']: s['reference'] for s in sections}

    result = {
        'matthew': [],
        'mark': [],
        'luke': [],
        'john': []
    }

    for entry in harmony:
        canon = entry['canon']
        sections = entry['sections']

        for gospel_cap, section_num in sections.items():
            gospel = gospel_cap.lower()
            if section_num not in section_data[gospel]:
                continue

            reference = section_data[gospel][section_num]

            try:
                verses = parse_verse_range(reference)
                for ch, v in verses:
                    result[gospel].append({
                        'chapter': ch,
                        'verse': v,
                        'canon': canon,
                        'section': section_num
                    })
            except:
                pass

    output_file = base_path / 'canon_lookup_full.json'

    with open(output_file, 'w') as f:
        f.write('[\n')

        seen = set()
        all_entries = []
        for gospel in ['matthew', 'mark', 'luke', 'john']:
            for entry in result[gospel]:
                key = (gospel, entry['chapter'], entry['verse'], entry['canon'], entry['section'])
                if key not in seen:
                    seen.add(key)
                    all_entries.append({
                        'gospel': gospel,
                        'chapter': entry['chapter'],
                        'verse': entry['verse'],
                        'canon': entry['canon'],
                        'section': entry['section']
                    })

        gospel_order = {'matthew': 0, 'mark': 1, 'luke': 2, 'john': 3}
        all_entries.sort(key=lambda x: (gospel_order[x['gospel']], x['chapter'], x['verse'], x['section'], x['canon']))

        for i, entry in enumerate(all_entries):
            comma = ',' if i < len(all_entries) - 1 else ''
            f.write(f'  {json.dumps(entry)}{comma}\n')

        f.write(']\n')

    print(f"✓ Generated {output_file}")
    for gospel in ['matthew', 'mark', 'luke', 'john']:
        print(f"  {gospel.capitalize()}: {len(result[gospel])} entries")

    matthew_1_17 = [e for e in result['matthew'] if e['chapter'] == 1 and e['verse'] == 17]
    if matthew_1_17:
        print(f"\nTest: Matthew 1:17 found in {len(matthew_1_17)} canon(s):")
        for e in matthew_1_17:
            print(f"  Canon {e['canon']}, Section {e['section']}")
    else:
        print("\nTest: Matthew 1:17 → NOT FOUND")

if __name__ == "__main__":
    main()

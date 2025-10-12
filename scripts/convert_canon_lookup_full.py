#!/usr/bin/env python3
import json
from pathlib import Path
from collections import defaultdict

def main():
    base_path = Path('texts/reference/eusebian_canons')

    with open(base_path / 'canon_lookup_full.json') as f:
        full_data = json.load(f)

    with open(base_path / 'data' / 'matthew_sections.json') as f:
        matthew_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'mark_sections.json') as f:
        mark_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'luke_sections.json') as f:
        luke_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'john_sections.json') as f:
        john_sections = {s['section']: s['reference'] for s in json.load(f)}

    section_map = {
        'matthew': matthew_sections,
        'mark': mark_sections,
        'luke': luke_sections,
        'john': john_sections
    }

    canon_lookup = {}
    canon_sections = defaultdict(lambda: defaultdict(set))

    for entry in full_data:
        gospel = entry['gospel']
        canon = entry['canon']
        section = entry['section']
        canon_key = f"{canon}.{section}"
        canon_sections[canon_key][gospel].add(section)

    canon_to_sections = defaultdict(lambda: defaultdict(set))
    for entry in full_data:
        gospel = entry['gospel']
        chapter = entry['chapter']
        verse = entry['verse']
        canon = entry['canon']
        section = entry['section']
        row_key = f"{canon}.{entry.get('canon_row', section)}"

        canon_to_sections[row_key][gospel].add(section)

    for canon_row in sorted(canon_to_sections.keys(), key=lambda x: (
        ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII'].index(x.split('.')[0]),
        int(x.split('.')[1])
    )):
        canon_lookup[canon_row] = {}
        for gospel in ['matthew', 'mark', 'luke', 'john']:
            sections = canon_to_sections[canon_row].get(gospel, set())
            if sections:
                section_num = min(sections)
                if section_num in section_map[gospel]:
                    reference = section_map[gospel][section_num].replace(':', '.')
                    canon_lookup[canon_row][gospel.capitalize()] = f"{section_num} - {reference}"

    output_file = base_path / 'canon_lookup.json'
    with open(output_file, 'w') as f:
        json.dump(canon_lookup, f, indent=2)

    print(f"✓ Generated {output_file} with {len(canon_lookup)} entries")

    canon_x_count = sum(1 for k in canon_lookup.keys() if k.startswith('X.'))
    print(f"  Canon X entries: {canon_x_count}")

    if 'X.2' in canon_lookup:
        print(f"\nSample Canon X.2:")
        for gospel, ref in canon_lookup['X.2'].items():
            print(f"  {gospel}: {ref}")

if __name__ == "__main__":
    main()

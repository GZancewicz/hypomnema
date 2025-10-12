#!/usr/bin/env python3
import json
from pathlib import Path

def main():
    base_path = Path('texts/reference/eusebian_canons')

    with open(base_path / 'harmony.json') as f:
        harmony = json.load(f)

    with open(base_path / 'data' / 'matthew_sections.json') as f:
        matthew_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'mark_sections.json') as f:
        mark_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'luke_sections.json') as f:
        luke_sections = {s['section']: s['reference'] for s in json.load(f)}
    with open(base_path / 'data' / 'john_sections.json') as f:
        john_sections = {s['section']: s['reference'] for s in json.load(f)}

    section_map = {
        'Matthew': matthew_sections,
        'Mark': mark_sections,
        'Luke': luke_sections,
        'John': john_sections
    }

    canon_lookup = {}
    canon_counts = {}

    for entry in harmony:
        canon = entry['canon']
        sections = entry['sections']

        if canon not in canon_counts:
            canon_counts[canon] = 0
        canon_counts[canon] += 1
        row_num = canon_counts[canon]

        canon_key = f"{canon}.{row_num}"
        canon_lookup[canon_key] = {}

        for gospel, section_num in sections.items():
            if section_num in section_map[gospel]:
                reference = section_map[gospel][section_num].replace(':', '.')
                canon_lookup[canon_key][gospel] = f"{section_num} - {reference}"

    output_file = base_path / 'canon_lookup.json'
    with open(output_file, 'w') as f:
        json.dump(canon_lookup, f, indent=2)

    print(f"✓ Generated {output_file} with {len(canon_lookup)} entries")

    canon_x_count = sum(1 for k in canon_lookup.keys() if k.startswith('X.'))
    canon_i_count = sum(1 for k in canon_lookup.keys() if k.startswith('I.'))
    print(f"  Canon I entries: {canon_i_count}")
    print(f"  Canon X entries: {canon_x_count}")

    if 'I.1' in canon_lookup:
        print(f"\nSample Canon I.1:")
        for gospel, ref in canon_lookup['I.1'].items():
            print(f"  {gospel}: {ref}")

    if 'X.2' in canon_lookup:
        print(f"\nSample Canon X.2:")
        for gospel, ref in canon_lookup['X.2'].items():
            print(f"  {gospel}: {ref}")

if __name__ == "__main__":
    main()

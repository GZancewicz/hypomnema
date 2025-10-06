#!/usr/bin/env python3

import json
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
canon_dir = os.path.join(project_root, 'texts', 'reference', 'eusebian_canons')

def load_section_data():
    section_data = {}
    for book in ['matthew', 'mark', 'luke', 'john']:
        file_path = os.path.join(canon_dir, 'data', f'{book}_sections.json')
        with open(file_path, 'r') as f:
            sections = json.load(f)
            section_data[book] = {str(s['section']): s['reference'] for s in sections}
    return section_data

def load_harmony_data():
    harmony_path = os.path.join(canon_dir, 'harmony.json')
    with open(harmony_path, 'r') as f:
        return json.load(f)

def reformat_canon_lookup():
    canon_lookup_path = os.path.join(canon_dir, 'canon_lookup.json')
    with open(canon_lookup_path, 'r') as f:
        canon_lookup = json.load(f)

    section_data = load_section_data()
    harmony_data = load_harmony_data()

    # Build a mapping from canon entry to sections
    canon_sections = {}
    for entry in harmony_data:
        canon = entry['canon']
        sections = entry['sections']

        # Create a unique key for this combination
        key = f"{canon}."
        matches = []
        for book in ['Matthew', 'Mark', 'Luke', 'John']:
            if book in sections:
                matches.append(f"{book}:{sections[book]}")
        matches_str = ','.join(sorted(matches))

        # Find the matching entry in canon_lookup
        for canon_key in canon_lookup:
            if canon_key.startswith(f"{canon}."):
                canon_sections[canon_key] = sections
                break

    # Create new format with section numbers
    new_lookup = {}
    for canon_key, verses in canon_lookup.items():
        new_entry = {}

        # Get sections for this canon entry from harmony
        canon_num = canon_key.split('.')[0]
        entry_num = int(canon_key.split('.')[1])

        # Find matching harmony entry
        matching_sections = None
        count = 0
        for h_entry in harmony_data:
            if h_entry['canon'] == canon_num:
                count += 1
                if count == entry_num:
                    matching_sections = h_entry['sections']
                    break

        if matching_sections:
            for book, verse_range in verses.items():
                book_lower = book.lower()
                if book in matching_sections:
                    section_num = str(matching_sections[book])
                    new_entry[book] = f"{section_num} - {verse_range}"
                else:
                    new_entry[book] = verse_range
        else:
            new_entry = verses

        new_lookup[canon_key] = new_entry

    # Save the reformatted data
    output_path = os.path.join(canon_dir, 'canon_lookup.json')
    with open(output_path, 'w') as f:
        json.dump(new_lookup, f, indent=2)

    print(f"Reformatted canon_lookup.json saved to {output_path}")
    print(f"Processed {len(new_lookup)} canon entries")

if __name__ == '__main__':
    reformat_canon_lookup()
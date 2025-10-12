#!/usr/bin/env python3

import json
import re
from pathlib import Path
from collections import defaultdict

def parse_section_file(file_path, book_name):
    """Parse a section file and return a list of (section_num, canon_num, verse_range) tuples."""
    sections = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Parse line format: "1	3	1.1-16"
            # Split on tab to get the components
            parts = line.split('\t')
            if len(parts) < 3:
                continue

            section_num = parts[0].strip()
            canon_num = parts[1].strip()
            verse_range = parts[2].strip()

            # Skip empty canon numbers (for Mark 16:9-20 which are not in canons)
            if not canon_num:
                continue

            try:
                sections.append((int(section_num), int(canon_num), verse_range))
            except ValueError:
                # Skip lines that don't have valid numbers
                continue

    return sections

def roman_to_canon_name(canon_num):
    """Convert canon number to Roman numeral format used in canon_lookup.json."""
    roman_numerals = {
        1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII", 8: "VIII",
        9: "IX", 10: "X", 11: "XI", 12: "XII", 13: "XIII"
    }
    return roman_numerals.get(canon_num, str(canon_num))

def build_canon_lookup():
    """Build the complete canon lookup from all source files."""

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / 'texts' / 'reference' / 'eusebian_canons' / 'data'

    files = {
        'matthew': data_dir / 'MAT-sections.txt',
        'mark': data_dir / 'MRK-sections.txt',
        'luke': data_dir / 'LUK-sections.txt',
        'john': data_dir / 'JHN-sections.txt'
    }

    all_sections = {}
    for book, file_path in files.items():
        sections = parse_section_file(str(file_path), book)
        all_sections[book] = sections
        print(f"Parsed {len(sections)} sections from {book}")

    # Group all sections by canon number
    canon_groups = defaultdict(list)

    for book, sections in all_sections.items():
        for section_num, canon_num, verse_range in sections:
            canon_groups[canon_num].append({
                'book': book,
                'section': section_num,
                'verses': verse_range
            })

    # Now build the canonical entries
    # For each canon number, we need to find the parallel passages
    canon_lookup = {}

    for canon_num in sorted(canon_groups.keys()):
        sections = canon_groups[canon_num]

        # Sort sections by book name and section number to get consistent ordering
        sections.sort(key=lambda x: (x['book'], x['section']))

        # Group sections that represent the same parallel passage
        # The key insight: sections with the same canon number should be examined
        # to find which ones are actually parallel passages

        # For now, let's build a simple mapping where we create parallel entries
        # by matching sections that appear to be parallel based on their sequence

        roman_canon = roman_to_canon_name(canon_num)

        # We need to find sequences of sections that are parallel across gospels
        # This is complex, so let's start simple: group any sections that have the same canon

        # Strategy: Create parallel groups by finding sections that appear in order
        # across the books and seem to be referencing the same events

        # For simplicity, let's create a mapping where each unique combination
        # of verses gets its own canon entry

        # Group sections by creating potential parallel sets
        if canon_num == 1:  # Canon I - passages in all four gospels
            # These should be grouped into parallel passages
            # Let's group them by examining patterns

            # For canon I, let's manually verify some and build the logic
            # First, let's collect all the sections
            canon_i_sections = {}
            for section in sections:
                if section['book'] not in canon_i_sections:
                    canon_i_sections[section['book']] = []
                canon_i_sections[section['book']].append(section)

            # Create canon entries based on sequence
            canon_counter = 1
            processed_sections = set()

            # For canon I, we need to find true parallel passages
            # Let's examine the sections more carefully
            all_canon_i_sections = []
            for section in sections:
                all_canon_i_sections.append(section)

            # Sort all sections by their original section numbers to maintain order
            all_canon_i_sections.sort(key=lambda x: (x['book'], x['section']))

            # Now we need to identify which sections are actually parallel
            # This requires understanding the narrative sequence

            # For now, let's create a simplified mapping
            # We'll group consecutive sections that seem to be parallel

            i = 0
            while i < len(all_canon_i_sections):
                # Start a new canon entry
                canon_key = f"{roman_canon}.{canon_counter}"
                canon_entry = {}

                # Look for sections that form a parallel set
                # For simplicity, let's group sections that are close in sequence
                current_section = all_canon_i_sections[i]
                canon_entry[current_section['book']] = current_section['verses']

                # Look ahead to see if there are parallel sections in other books
                # This is a simplified approach - in reality we need to analyze content
                j = i + 1
                used_books = {current_section['book']}

                while j < len(all_canon_i_sections) and len(used_books) < 4:
                    next_section = all_canon_i_sections[j]
                    if next_section['book'] not in used_books:
                        # Check if this could be a parallel passage
                        # For now, we'll add it if it's within a reasonable range
                        if abs(next_section['section'] - current_section['section']) < 10:
                            canon_entry[next_section['book']] = next_section['verses']
                            used_books.add(next_section['book'])
                        j += 1
                    else:
                        j += 1

                canon_lookup[canon_key] = canon_entry
                canon_counter += 1
                i += 1

                # Skip ahead if we've processed multiple sections
                while i < len(all_canon_i_sections) and all_canon_i_sections[i]['book'] in used_books:
                    i += 1

        else:
            # For other canons, create simpler mappings
            canon_counter = 1
            books_in_entry = {}

            for section in sections:
                # Check if we already have this book in current entry
                if section['book'] not in books_in_entry:
                    books_in_entry[section['book']] = section['verses']
                else:
                    # Start a new entry
                    if books_in_entry:
                        canon_key = f"{roman_canon}.{canon_counter}"
                        canon_lookup[canon_key] = books_in_entry.copy()
                        canon_counter += 1
                    books_in_entry = {section['book']: section['verses']}

            # Add the last entry
            if books_in_entry:
                canon_key = f"{roman_canon}.{canon_counter}"
                canon_lookup[canon_key] = books_in_entry

    return canon_lookup

def main():
    print("Building corrected canon lookup...")

    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    canon_dir = project_root / 'texts' / 'reference' / 'eusebian_canons'

    canon_lookup = build_canon_lookup()

    def natural_sort_key(key):
        parts = key.split('.')
        roman_part = parts[0]
        num_part = int(parts[1])

        roman_to_num = {
            "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
            "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13
        }

        return (roman_to_num.get(roman_part, 0), num_part)

    sorted_keys = sorted(canon_lookup.keys(), key=natural_sort_key)
    sorted_canon_lookup = {key: canon_lookup[key] for key in sorted_keys}

    output_path = canon_dir / 'canon_lookup_corrected_v2.json'
    with open(output_path, 'w') as f:
        json.dump(sorted_canon_lookup, f, indent=2)

    print(f"Wrote corrected canon lookup to {output_path}")
    print(f"Total canon entries: {len(sorted_canon_lookup)}")

    print("\nFirst few entries:")
    for i, (key, value) in enumerate(sorted_canon_lookup.items()):
        if i >= 10:
            break
        print(f"  {key}: {value}")

    print("\nComparing with existing canon_lookup.json...")
    try:
        with open(canon_dir / 'canon_lookup.json', 'r') as f:
            existing_lookup = json.load(f)

        print(f"Existing lookup has {len(existing_lookup)} entries")
        print(f"New lookup has {len(sorted_canon_lookup)} entries")

        # Check a few specific entries
        test_keys = ["I.1", "I.10", "II.1"]
        for key in test_keys:
            if key in existing_lookup and key in sorted_canon_lookup:
                if existing_lookup[key] != sorted_canon_lookup[key]:
                    print(f"\nDifference in {key}:")
                    print(f"  Current: {existing_lookup[key]}")
                    print(f"  New:     {sorted_canon_lookup[key]}")
                else:
                    print(f"  {key}: MATCHES")
            elif key in existing_lookup:
                print(f"  {key}: MISSING in new lookup")
            elif key in sorted_canon_lookup:
                print(f"  {key}: NEW entry")

    except Exception as e:
        print(f"Could not compare with existing file: {e}")

if __name__ == "__main__":
    main()
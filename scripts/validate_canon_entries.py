#!/usr/bin/env python3

import json
import re
from collections import defaultdict

def parse_section_file(file_path, book_name):
    """Parse a section file and return a dict mapping verse ranges to canon numbers."""
    verse_to_canon = {}
    canon_to_verses = defaultdict(list)

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split('\t')
            if len(parts) < 3:
                continue

            section_num = parts[0].strip()
            canon_num = parts[1].strip()
            verse_range = parts[2].strip()

            if not canon_num:
                continue

            try:
                # Handle multiple canon numbers like "1,4"
                if ',' in canon_num:
                    canon_nums = [int(x.strip()) for x in canon_num.split(',')]
                    for cn in canon_nums:
                        verse_to_canon[verse_range] = cn  # Note: this will overwrite, but that's ok for validation
                        canon_to_verses[cn].append(verse_range)
                else:
                    canon_num = int(canon_num)
                    verse_to_canon[verse_range] = canon_num
                    canon_to_verses[canon_num].append(verse_range)
            except ValueError:
                continue

    return verse_to_canon, canon_to_verses

def main():
    print("Validating canon entries against source files...")

    # File paths
    files = {
        'matthew': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/MAT-sections.txt',
        'mark': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/MRK-sections.txt',
        'luke': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/LUK-sections.txt',
        'john': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/JHN-sections.txt'
    }

    # Parse all source files
    source_data = {}
    for book, file_path in files.items():
        verse_to_canon, canon_to_verses = parse_section_file(file_path, book)
        source_data[book] = {
            'verse_to_canon': verse_to_canon,
            'canon_to_verses': canon_to_verses
        }
        print(f"Parsed {book}: {len(verse_to_canon)} verse ranges")

    # Load current canon_lookup.json
    with open('/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/canon_lookup.json', 'r') as f:
        current_lookup = json.load(f)

    print(f"Current canon_lookup.json has {len(current_lookup)} entries")

    # Validate each entry in current_lookup
    errors = []
    corrections = {}

    for canon_key, canon_entry in current_lookup.items():
        print(f"\nValidating {canon_key}...")

        for book, verse_range in canon_entry.items():
            if book in source_data:
                # Check if this verse range exists in the source
                verse_to_canon = source_data[book]['verse_to_canon']

                if verse_range in verse_to_canon:
                    source_canon = verse_to_canon[verse_range]
                    print(f"  {book} {verse_range} -> Canon {source_canon} ✓")
                else:
                    # Try to find the closest match
                    closest_matches = []
                    for source_verse, source_canon in verse_to_canon.items():
                        if verse_range in source_verse or source_verse in verse_range:
                            closest_matches.append((source_verse, source_canon))

                    if closest_matches:
                        print(f"  {book} {verse_range} -> NOT FOUND, closest matches:")
                        for match_verse, match_canon in closest_matches[:3]:
                            print(f"    {match_verse} (Canon {match_canon})")

                        # Use the first close match for correction
                        correct_verse, correct_canon = closest_matches[0]
                        if canon_key not in corrections:
                            corrections[canon_key] = {}
                        corrections[canon_key][book] = correct_verse

                        errors.append({
                            'canon_key': canon_key,
                            'book': book,
                            'current_verse': verse_range,
                            'suggested_verse': correct_verse,
                            'source_canon': correct_canon
                        })
                    else:
                        print(f"  {book} {verse_range} -> NOT FOUND ❌")
                        errors.append({
                            'canon_key': canon_key,
                            'book': book,
                            'current_verse': verse_range,
                            'suggested_verse': None,
                            'source_canon': None
                        })

    print(f"\n\nSUMMARY:")
    print(f"Found {len(errors)} errors")

    # Group errors by type
    not_found = [e for e in errors if e['suggested_verse'] is None]
    incorrect = [e for e in errors if e['suggested_verse'] is not None]

    print(f"- {len(not_found)} verse ranges not found in source")
    print(f"- {len(incorrect)} verse ranges with suggested corrections")

    if incorrect:
        print(f"\nSuggested corrections:")
        for error in incorrect[:10]:  # Show first 10
            print(f"  {error['canon_key']} {error['book']}: {error['current_verse']} -> {error['suggested_verse']}")

    # Create a corrected version
    if corrections:
        corrected_lookup = current_lookup.copy()

        for canon_key, book_corrections in corrections.items():
            if canon_key in corrected_lookup:
                for book, correct_verse in book_corrections.items():
                    corrected_lookup[canon_key][book] = correct_verse

        # Save corrected version
        output_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/canon_lookup_corrected_simple.json'
        with open(output_path, 'w') as f:
            json.dump(corrected_lookup, f, indent=2)

        print(f"\nSaved corrected version to {output_path}")
        print(f"Applied {len(corrections)} corrections")

    # Show some specific examples of validation
    print(f"\nExamples of validation:")
    test_entries = ["I.1", "I.10", "II.1"]
    for test_key in test_entries:
        if test_key in current_lookup:
            print(f"\n{test_key}:")
            for book, verse in current_lookup[test_key].items():
                if book in source_data and verse in source_data[book]['verse_to_canon']:
                    canon_num = source_data[book]['verse_to_canon'][verse]
                    print(f"  {book} {verse} -> Canon {canon_num}")
                else:
                    print(f"  {book} {verse} -> NOT FOUND")

if __name__ == "__main__":
    main()
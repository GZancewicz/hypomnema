#!/usr/bin/env python3

import json
import re
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

    # File paths
    files = {
        'matthew': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/MAT-sections.txt',
        'mark': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/MRK-sections.txt',
        'luke': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/LUK-sections.txt',
        'john': '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/data/JHN-sections.txt'
    }

    # Parse all files
    all_sections = {}
    for book, file_path in files.items():
        sections = parse_section_file(file_path, book)
        all_sections[book] = sections
        print(f"Parsed {len(sections)} sections from {book}")

    # Create a map from section numbers to their canonical data for each book
    section_to_canon = {}
    for book, sections in all_sections.items():
        section_to_canon[book] = {}
        for section_num, canon_num, verse_range in sections:
            section_to_canon[book][section_num] = {
                'canon': canon_num,
                'verses': verse_range
            }

    # Build canonical lookup by gathering all sections that refer to the same passages
    # This is more complex - we need to analyze the actual parallel passages
    canon_lookup = {}

    # Gather all section-canon-verse mappings
    all_mappings = []
    for book, sections in all_sections.items():
        for section_num, canon_num, verse_range in sections:
            all_mappings.append({
                'book': book,
                'section': section_num,
                'canon': canon_num,
                'verses': verse_range
            })

    # Group by canon number first
    canons_data = defaultdict(list)
    for mapping in all_mappings:
        canons_data[mapping['canon']].append(mapping)

    # For each canon, we need to identify parallel passages
    # The key insight: sections with the same canon number are parallel passages
    # But we need to group them correctly based on the actual section sequence

    for canon_num in sorted(canons_data.keys()):
        canon_mappings = canons_data[canon_num]

        # Sort by book and section to understand the sequence
        canon_mappings.sort(key=lambda x: (x['book'], x['section']))

        # Group mappings that are truly parallel
        # For now, we'll group all sections with the same canon sequentially
        roman_canon = roman_to_canon_name(canon_num)

        # Create a running counter for this canon
        canon_counter = 1

        # Track which sections we've already processed to avoid duplicates
        processed_sections = set()

        for mapping in canon_mappings:
            section_key = (mapping['book'], mapping['section'])
            if section_key in processed_sections:
                continue

            # Start a new canon entry
            canon_key = f"{roman_canon}.{canon_counter}"

            # Find all parallel sections for this one
            # For simplicity, we'll just add this single section
            # In a more sophisticated approach, we would find actual parallels
            canon_lookup[canon_key] = {mapping['book']: mapping['verses']}

            processed_sections.add(section_key)
            canon_counter += 1

    return canon_lookup

def main():
    print("Building corrected canon lookup...")

    canon_lookup = build_canon_lookup()

    # Sort the keys naturally (I.1, I.2, ... I.10, ...)
    def natural_sort_key(key):
        parts = key.split('.')
        roman_part = parts[0]
        num_part = int(parts[1])

        # Convert roman to number for sorting
        roman_to_num = {
            "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8,
            "IX": 9, "X": 10, "XI": 11, "XII": 12, "XIII": 13
        }

        return (roman_to_num.get(roman_part, 0), num_part)

    sorted_keys = sorted(canon_lookup.keys(), key=natural_sort_key)
    sorted_canon_lookup = {key: canon_lookup[key] for key in sorted_keys}

    # Write the corrected canon lookup
    output_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/reference/eusebian_canons/canon_lookup_corrected.json'
    with open(output_path, 'w') as f:
        json.dump(sorted_canon_lookup, f, indent=2)

    print(f"Wrote corrected canon lookup to {output_path}")
    print(f"Total canon entries: {len(sorted_canon_lookup)}")

    # Show some examples
    print("\nFirst few entries:")
    for i, (key, value) in enumerate(sorted_canon_lookup.items()):
        if i >= 5:
            break
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
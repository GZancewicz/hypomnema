#!/usr/bin/env python3
import json
import re

def parse_verse_range(verse_str):
    """Parse a verse range like '1:1-3' or '1:1' into individual verses"""
    verses = []

    # Handle ranges like "3:13-17" or "1:9-11"
    if '-' in verse_str:
        parts = verse_str.split(':')
        if len(parts) == 2:
            chapter = int(parts[0])
            verse_range = parts[1]
            if '-' in verse_range:
                start, end = verse_range.split('-')
                for v in range(int(start), int(end) + 1):
                    verses.append(f"{chapter}:{v}")
            else:
                verses.append(verse_str)
    else:
        verses.append(verse_str)

    return verses

def check_consistency():
    # Load the JSON files
    with open('../texts/reference/eusebian_canons/verse_to_canon.json', 'r') as f:
        verse_to_canon = json.load(f)

    with open('../texts/reference/eusebian_canons/canon_lookup.json', 'r') as f:
        canon_lookup = json.load(f)

    issues = []
    matches = 0

    print("Checking consistency between verse_to_canon.json and canon_lookup.json...")
    print("=" * 60)

    # Check 1: Every verse in verse_to_canon should have its canon in canon_lookup
    print("\n1. Checking if all verse_to_canon entries exist in canon_lookup...")
    for book, verses in verse_to_canon.items():
        for verse, canon in verses.items():
            if canon not in canon_lookup:
                issues.append(f"Canon {canon} from {book} {verse} not found in canon_lookup")
            else:
                matches += 1

    if not issues:
        print(f"✓ All {matches} canon references from verse_to_canon exist in canon_lookup")
    else:
        print(f"✗ Found {len(issues)} missing canon references:")
        for issue in issues[:10]:  # Show first 10
            print(f"  - {issue}")

    # Check 2: Every verse in canon_lookup should be in verse_to_canon
    print("\n2. Checking if all canon_lookup verses are in verse_to_canon...")
    reverse_issues = []
    reverse_matches = 0

    for canon, books in canon_lookup.items():
        for book, verse_range in books.items():
            if book in verse_to_canon:
                # Parse the verse range
                verses = parse_verse_range(verse_range)
                for verse in verses:
                    if verse in verse_to_canon[book]:
                        canon_val = verse_to_canon[book][verse]
                        if canon_val != canon:
                            reverse_issues.append(
                                f"{book} {verse} has canon {canon_val} in verse_to_canon "
                                f"but is listed under {canon} in canon_lookup"
                            )
                        else:
                            reverse_matches += 1
                    else:
                        # This verse from canon_lookup is not in verse_to_canon
                        # This might be expected for verse ranges
                        pass

    if not reverse_issues:
        print(f"✓ {reverse_matches} verses matched correctly between both files")
    else:
        print(f"✗ Found {len(reverse_issues)} canon mismatches:")
        for issue in reverse_issues[:10]:  # Show first 10
            print(f"  - {issue}")

    # Check 3: Sample specific verses
    print("\n3. Checking specific example verses...")
    test_cases = [
        ("matthew", "1:1"),
        ("matthew", "1:17"),
        ("matthew", "1:22"),
        ("john", "1:1"),
        ("luke", "1:1"),
    ]

    for book, verse in test_cases:
        if book in verse_to_canon and verse in verse_to_canon[book]:
            canon = verse_to_canon[book][verse]
            print(f"  {book.capitalize()} {verse} -> Canon {canon}")

            # Check if this canon has the verse in canon_lookup
            if canon in canon_lookup and book in canon_lookup[canon]:
                print(f"    ✓ Found in canon_lookup: {canon_lookup[canon][book]}")
            else:
                print(f"    ✗ Not found in canon_lookup under {canon}")
        else:
            print(f"  {book.capitalize()} {verse} -> No canon entry")

    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(f"Total verses in verse_to_canon: {sum(len(v) for v in verse_to_canon.values())}")
    print(f"Total canons in canon_lookup: {len(canon_lookup)}")
    print(f"Total issues found: {len(issues) + len(reverse_issues)}")

    return len(issues) + len(reverse_issues) == 0

if __name__ == "__main__":
    is_consistent = check_consistency()
    if is_consistent:
        print("\n✓ Files are consistent!")
    else:
        print("\n✗ Files have consistency issues")
#!/usr/bin/env python3
"""
Generate a mapping from verses to ALL homilies that start at that verse.
Allows multiple homilies per verse.
"""

import json
from pathlib import Path

def main():
    # Load the homily coverage data
    coverage_path = Path("../texts/commentaries/chrysostom/matthew/homily_coverage_complete.json")
    
    with open(coverage_path, 'r') as f:
        homily_coverage = json.load(f)
    
    # Create verse-to-homilies mapping (allowing multiple homilies per verse)
    verse_to_homilies = {}
    
    for homily_num_str, data in homily_coverage.items():
        # Create the verse key
        verse_key = f"{data['start_chapter']}:{data['start_verse']}"
        
        # Initialize array if not exists
        if verse_key not in verse_to_homilies:
            verse_to_homilies[verse_key] = []
        
        # Add this homily to the array
        verse_to_homilies[verse_key].append({
            "homily_number": data["homily_number"],
            "homily_roman": data["homily_roman"],
            "passage": f"Matthew {data['start_chapter']}:{data['start_verse']}",
            "end": f"Matthew {data['end_chapter']}:{data['end_verse']}"
        })
    
    # Sort homilies within each verse by homily number
    for verse_key in verse_to_homilies:
        verse_to_homilies[verse_key].sort(key=lambda x: x["homily_number"])
    
    # Save the mapping
    output_path = Path("../texts/commentaries/chrysostom/matthew/matthew_verse_to_homilies.json")
    with open(output_path, 'w') as f:
        json.dump(verse_to_homilies, f, indent=2, sort_keys=True)
    
    print(f"Saved verse-to-homilies mapping to {output_path}")
    
    # Print statistics
    print(f"\nTotal verses with homilies: {len(verse_to_homilies)}")
    
    # Show verses with multiple homilies
    multi_homily_verses = {k: v for k, v in verse_to_homilies.items() if len(v) > 1}
    if multi_homily_verses:
        print(f"\nVerses with multiple homilies:")
        for verse, homilies in sorted(multi_homily_verses.items()):
            homily_nums = [h["homily_roman"] for h in homilies]
            print(f"  Matthew {verse}: {', '.join(homily_nums)}")

if __name__ == "__main__":
    main()
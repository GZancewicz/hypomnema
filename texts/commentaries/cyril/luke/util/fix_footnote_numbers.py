#!/usr/bin/env python3

import json
import re
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    content_dir = base_dir / 'content'

    # Load coverage.json to get list of sermons
    coverage_file = base_dir / 'coverage.json'
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)

    fixed_count = 0

    for homily_data in coverage_data['homilies']:
        sermon_id = homily_data['id']
        sermon_dir = content_dir / f'{sermon_id:03d}'

        content_file = sermon_dir / 'content.json'
        metadata_file = sermon_dir / 'metadata.json'

        if not content_file.exists() or not metadata_file.exists():
            continue

        # Load content and metadata
        with open(content_file, 'r') as f:
            content_data = json.load(f)

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        footnotes = metadata.get('footnotes', {})
        if not footnotes:
            continue

        # Build mapping of what footnote numbers exist in the text
        # Find all <sup>fN</sup> markers in content
        all_text = '\n'.join(content_data.get('paragraphs', []))
        found_markers = set(re.findall(r'<sup>f(\d+)</sup>', all_text))

        if not found_markers:
            continue

        # Sort the original footnote numbers
        old_numbers = sorted([int(n) for n in found_markers])

        # Create mapping: old number → new number (1, 2, 3...)
        renumber_map = {str(old): str(i) for i, old in enumerate(old_numbers, 1)}

        # Update paragraphs
        updated_paragraphs = []
        for paragraph in content_data.get('paragraphs', []):
            # Replace each footnote marker with renumbered version
            for old_num, new_num in renumber_map.items():
                paragraph = paragraph.replace(f'<sup>f{old_num}</sup>', f'<sup>{new_num}</sup>')
            updated_paragraphs.append(paragraph)

        # Save updated content
        content_data['paragraphs'] = updated_paragraphs
        with open(content_file, 'w') as f:
            json.dump(content_data, f, indent=2)

        fixed_count += 1
        print(f"Fixed Sermon {sermon_id}: {len(renumber_map)} footnotes renumbered")

    print(f"\nTotal sermons fixed: {fixed_count}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def roman_to_int(roman):
    """Convert Roman numeral to integer"""
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_value = 0
    for char in reversed(roman.upper()):
        value = roman_values.get(char, 0)
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    numerals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    result = ''
    for i, value in enumerate(values):
        count = num // value
        if count:
            result += numerals[i] * count
            num -= value * count
    return result

def extract_footnotes_from_html(html_file, sermon_start_id, sermon_end_id):
    """Extract footnotes that belong to a specific sermon range"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')

    # Find all footnote references in the sermon section
    footnote_refs = set()

    # Find the sermon start anchor
    start_anchor = soup.find('a', {'name': f'C{sermon_start_id}'})
    if not start_anchor:
        return {}

    # Find the sermon end anchor (next sermon)
    end_anchor = soup.find('a', {'name': f'C{sermon_end_id}'})

    # Collect all footnote references between start and end
    current = start_anchor
    while current:
        if end_anchor and current == end_anchor:
            break

        # Look for footnote references <A HREF="#N"><SUP>N</SUP></A>
        if current.name == 'a' and current.get('href', '').startswith('#'):
            sup = current.find('sup')
            if sup:
                footnote_num = sup.get_text().strip()
                if footnote_num.isdigit():
                    footnote_refs.add(footnote_num)

        # Check all descendants for footnote refs
        if hasattr(current, 'descendants'):
            for tag in current.descendants:
                if hasattr(tag, 'name') and tag.name == 'a' and tag.get('href', '').startswith('#'):
                    sup = tag.find('sup')
                    if sup:
                        footnote_num = sup.get_text().strip()
                        if footnote_num.isdigit():
                            footnote_refs.add(footnote_num)

        current = current.find_next()

    # Now extract the actual footnote text
    footnotes = {}
    for num in footnote_refs:
        footnote_anchor = soup.find('a', {'name': num})
        if footnote_anchor:
            # Get the parent paragraph
            parent = footnote_anchor.parent
            if parent:
                # Extract text, removing the number and letter prefix
                text = parent.get_text()
                # Remove the footnote number and letter (e.g., "1. a ")
                text = re.sub(r'^\d+\.\s*[a-z]\s*', '', text)
                footnotes[num] = text.strip()

    # Renumber footnotes starting from 1
    renumbered = {}
    for i, (old_num, text) in enumerate(sorted(footnotes.items(), key=lambda x: int(x[0])), 1):
        renumbered[str(i)] = text

    return renumbered

def main():
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    content_dir = base_dir / 'content'
    source_dir = base_dir / 'source'

    # Load coverage.json for scripture references
    coverage_file = base_dir / 'coverage.json'
    with open(coverage_file, 'r') as f:
        coverage_data = json.load(f)

    # Map HTML files to sermon ranges
    file_mappings = {
        'cyril_on_luke_01_sermons_01_11.htm': (1, 11),
        'cyril_on_luke_02_sermons_12_25.htm': (12, 25),
        'cyril_on_luke_03_sermons_26_38.htm': (26, 38),
        'cyril_on_luke_04_sermons_39_46.htm': (39, 46),
        'cyril_on_luke_05_sermons_47_56.htm': (47, 56),
        'cyril_on_luke_06_sermons_57_65.htm': (57, 65),
        'cyril_on_luke_07_sermons_66_80.htm': (66, 80),
        'cyril_on_luke_08_sermons_81_88.htm': (81, 88),
        'cyril_on_luke_09_sermons_89_98.htm': (89, 98),
        'cyril_on_luke_10_sermons_99_109.htm': (99, 109),
        'cyril_on_luke_11_sermons_110_123.htm': (110, 123),
        'cyril_on_luke_12_sermons_124_134.htm': (124, 134),
        'cyril_on_luke_13_sermons_135_145.htm': (135, 145),
        'cyril_on_luke_14_sermons_146_156.htm': (146, 156),
    }

    created_count = 0

    for homily_data in coverage_data['homilies']:
        sermon_id = homily_data['id']
        sermon_dir = content_dir / f'{sermon_id:03d}'

        if not sermon_dir.exists():
            print(f"Warning: Directory not found for Sermon {sermon_id}")
            continue

        # Load existing content.json
        content_file = sermon_dir / 'content.json'
        if not content_file.exists():
            print(f"Warning: content.json not found for Sermon {sermon_id}")
            continue

        with open(content_file, 'r') as f:
            content_data = json.load(f)

        # Calculate word count
        all_text = ' '.join(content_data.get('paragraphs', []))
        word_count = len(all_text.split())

        # Create excerpt (first 200 words)
        words = all_text.split()[:200]
        excerpt = ' '.join(words) + '...' if len(words) == 200 else ' '.join(words)

        # Find which HTML file contains this sermon
        html_file = None
        for filename, (start, end) in file_mappings.items():
            if start <= sermon_id <= end:
                html_file = source_dir / filename
                break

        # Extract footnotes
        footnotes = {}
        has_footnotes = False
        if html_file and html_file.exists():
            # Find the next sermon ID for boundary
            next_sermon_id = sermon_id + 1
            footnotes = extract_footnotes_from_html(html_file, sermon_id, next_sermon_id)
            has_footnotes = len(footnotes) > 0

        # Build scripture reference
        scripture_ref = None
        if 'start' in homily_data and 'end' in homily_data:
            start = homily_data['start']
            end = homily_data['end']

            # Build display string
            if start['chapter'] == end['chapter'] and start['verse'] == end['verse']:
                display = f"Luke {start['chapter']}:{start['verse']}"
            elif start['chapter'] == end['chapter']:
                display = f"Luke {start['chapter']}:{start['verse']}-{end['verse']}"
            else:
                display = f"Luke {start['chapter']}:{start['verse']}-{end['chapter']}:{end['verse']}"

            scripture_ref = {
                "book": "luke",
                "start": start,
                "end": end,
                "display": display
            }

        # Create metadata
        metadata = {
            "id": sermon_id,
            "roman": int_to_roman(sermon_id),
            "title": f"Sermon {int_to_roman(sermon_id)}",
            "subtitle": scripture_ref['display'] if scripture_ref else "",
            "author": "cyril",
            "author_full": "Cyril of Alexandria",
            "work": "Sermons on Luke",
            "scripture_reference": scripture_ref,
            "themes": [],
            "date_delivered": None,
            "word_count": word_count,
            "excerpt": excerpt,
            "source_file": html_file.name if html_file else "",
            "extraction_method": "html_parsing",
            "has_footnotes": has_footnotes,
            "footnotes": footnotes,
            "verified": True
        }

        # Save metadata.json
        metadata_file = sermon_dir / 'metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        created_count += 1
        print(f"Created metadata for Sermon {sermon_id}: {scripture_ref['display'] if scripture_ref else 'No reference'} ({len(footnotes)} footnotes)")

    print(f"\nTotal metadata files created: {created_count}")

if __name__ == "__main__":
    main()

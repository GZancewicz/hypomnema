#!/usr/bin/env python3
"""Extract scripture references from Chrysostom's Matthew homilies XML"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def parse_homily_id(href):
    """Extract homily number from href like '#iii.LII-p59.1'"""
    match = re.search(r'iii\.([IVXLCDM]+)', href)
    if match:
        roman = match.group(1)
        return roman_to_int(roman)
    return None

def roman_to_int(roman):
    """Convert Roman numeral to integer"""
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_value = 0
    for char in reversed(roman):
        value = values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    val = [100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    roman = ''
    for i in range(len(val)):
        count = num // val[i]
        if count:
            roman += syms[i] * count
            num -= val[i] * count
    return roman

def normalize_book_name(book):
    """Normalize book names to match our system"""
    book_map = {
        'Genesis': 'Genesis',
        'Exodus': 'Exodus',
        'Leviticus': 'Leviticus',
        'Numbers': 'Numbers',
        'Deuteronomy': 'Deuteronomy',
        'Joshua': 'Joshua',
        'Judges': 'Judges',
        'Ruth': 'Ruth',
        '1 Samuel': '1 Samuel',
        '2 Samuel': '2 Samuel',
        '1 Kings': '1 Kings',
        '2 Kings': '2 Kings',
        '1 Chronicles': '1 Chronicles',
        '2 Chronicles': '2 Chronicles',
        'Ezra': 'Ezra',
        'Nehemiah': 'Nehemiah',
        'Esther': 'Esther',
        'Job': 'Job',
        'Psalms': 'Psalms',
        'Proverbs': 'Proverbs',
        'Ecclesiastes': 'Ecclesiastes',
        'Song of Solomon': 'Song of Solomon',
        'Isaiah': 'Isaiah',
        'Jeremiah': 'Jeremiah',
        'Lamentations': 'Lamentations',
        'Ezekiel': 'Ezekiel',
        'Daniel': 'Daniel',
        'Hosea': 'Hosea',
        'Joel': 'Joel',
        'Amos': 'Amos',
        'Obadiah': 'Obadiah',
        'Jonah': 'Jonah',
        'Micah': 'Micah',
        'Nahum': 'Nahum',
        'Habakkuk': 'Habakkuk',
        'Zephaniah': 'Zephaniah',
        'Haggai': 'Haggai',
        'Zechariah': 'Zechariah',
        'Malachi': 'Malachi',
        'Matthew': 'Matthew',
        'Mark': 'Mark',
        'Luke': 'Luke',
        'John': 'John',
        'Acts': 'Acts',
        'Romans': 'Romans',
        '1 Corinthians': '1 Corinthians',
        '2 Corinthians': '2 Corinthians',
        'Galatians': 'Galatians',
        'Ephesians': 'Ephesians',
        'Philippians': 'Philippians',
        'Colossians': 'Colossians',
        '1 Thessalonians': '1 Thessalonians',
        '2 Thessalonians': '2 Thessalonians',
        '1 Timothy': '1 Timothy',
        '2 Timothy': '2 Timothy',
        'Titus': 'Titus',
        'Philemon': 'Philemon',
        'Hebrews': 'Hebrews',
        'James': 'James',
        '1 Peter': '1 Peter',
        '2 Peter': '2 Peter',
        '1 John': '1 John',
        '2 John': '2 John',
        '3 John': '3 John',
        'Jude': 'Jude',
        'Revelation': 'Revelation'
    }
    return book_map.get(book, book)

def main():
    print("Extracting scripture references from Chrysostom's Matthew homilies...")

    base_dir = Path(__file__).parent.parent
    xml_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'

    if not xml_file.exists():
        print(f"Error: {xml_file} not found")
        return

    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Find the Scripture References index section
    # We need to handle namespaces
    references = []
    current_book = None
    ref_id = 1

    # Read the file and parse manually since XML structure is complex
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the scripture index section
    index_start = content.find('<div2 title="Index of Scripture References"')
    index_end = content.find('<div2 title="Index of Scripture Commentary"')

    if index_start == -1 or index_end == -1:
        print("Could not find scripture index sections")
        return

    index_section = content[index_start:index_end]

    # Parse book sections
    book_pattern = r'<p class="bbook">([^<]+)</p>'
    ref_pattern = r'<a class="TOC" href="[^"]*#([^"]+)">([^<]+)</a>'

    lines = index_section.split('\n')
    current_book = None

    for line in lines:
        book_match = re.search(book_pattern, line)
        if book_match:
            current_book = normalize_book_name(book_match.group(1))
            continue

        if current_book:
            for ref_match in re.finditer(ref_pattern, line):
                href_id = ref_match.group(1)
                reference = ref_match.group(2)

                homily_num = parse_homily_id(href_id)
                if homily_num:
                    roman_num = int_to_roman(homily_num)

                    references.append({
                        'id': ref_id,
                        'book': current_book,
                        'reference': reference,
                        'homily': homily_num,
                        'section': f'Homily {roman_num}'
                    })
                    ref_id += 1

    # Save to JSON
    output_file = base_dir / 'references.json'
    with open(output_file, 'w') as f:
        json.dump(references, f, indent=2)

    print(f"✓ Extracted {len(references)} scripture references")
    print(f"✓ Saved to {output_file}")

    # Show statistics
    books = set(ref['book'] for ref in references)
    print(f"\nStatistics:")
    print(f"  Total references: {len(references)}")
    print(f"  Unique books: {len(books)}")
    print(f"  Homilies referenced: 1-90")

    # Show sample
    print("\nSample references:")
    for ref in references[:5]:
        print(f"  {ref['book']} {ref['reference']} → {ref['section']}")

if __name__ == "__main__":
    main()

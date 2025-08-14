#!/usr/bin/env python3
"""
Complete parser for Chrysostom Matthew ThML source.
Generates all JSON files with proper structure.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import html

def clean_text(text):
    """Clean text while preserving structure."""
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def to_roman(num):
    """Convert number to Roman numeral."""
    values = [
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    result = ''
    for value, letter in values:
        count = num // value
        if count:
            result += letter * count
            num -= value * count
    return result

def extract_homily_boundaries(soup):
    """Find all homily boundaries in the document."""
    boundaries = {}
    
    # Find all elements containing "Homily" text
    for elem in soup.find_all(string=re.compile(r'Homily\s+[IVX]+\.')):
        # Extract homily number
        match = re.search(r'Homily\s+([IVX]+)\.', elem)
        if match:
            roman = match.group(1)
            # Convert roman to number
            num = roman_to_int(roman)
            if num:
                parent = elem.parent
                boundaries[num] = parent
    
    return boundaries

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    total = 0
    prev = 0
    for char in reversed(roman):
        if char in values:
            val = values[char]
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
    return total if total > 0 else None

def extract_homily_content(soup, homily_num, boundaries):
    """Extract content for a specific homily."""
    if homily_num not in boundaries:
        return None, {}
    
    start_elem = boundaries[homily_num]
    end_elem = boundaries.get(homily_num + 1)
    
    content = {
        'title': f'Homily {to_roman(homily_num)}',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_counter = 0
    
    # Look for subtitle (scripture reference)
    current = start_elem
    subtitle_found = False
    
    while current and not subtitle_found:
        if current.name == 'p':
            text = current.get_text()
            # Look for Matt/Matthew reference
            match = re.search(r'Matt?(?:hew)?\.?\s*(\d+)[:\.](\d+(?:-\d+)?)', text)
            if match:
                content['subtitle'] = f"Matthew {match.group(1)}:{match.group(2)}"
                subtitle_found = True
                break
        current = current.next_sibling
    
    # Reset to start for content extraction
    current = start_elem.next_sibling if start_elem else None
    
    while current and current != end_elem:
        if current.name == 'p':
            para_text = ""
            
            # Process paragraph content
            for elem in current.descendants:
                if isinstance(elem, NavigableString):
                    para_text += str(elem)
                elif elem.name == 'note':
                    # Extract footnote
                    footnote_counter += 1
                    fn_id = str(footnote_counter)
                    
                    # Get footnote text
                    endnote = elem.find('p', class_='endnote')
                    if endnote:
                        fn_text = clean_text(endnote.get_text())
                        footnotes[fn_id] = fn_text
                    else:
                        # Try to get any text in the note
                        fn_text = clean_text(elem.get_text())
                        if fn_text:
                            footnotes[fn_id] = fn_text
                    
                    para_text += f'<sup>f{fn_id}</sup>'
            
            para_text = clean_text(para_text)
            
            # Skip if it's a title or empty
            if para_text and not re.match(r'^(Homily|HOMILY)\s+[IVX]+\.', para_text):
                content['paragraphs'].append(para_text)
        
        current = current.next_sibling
    
    return content, footnotes

def extract_scripture_reference(subtitle):
    """Extract structured scripture reference from subtitle."""
    if not subtitle:
        return None
    
    match = re.search(r'Matthew\s+(\d+)[:\.](\d+)(?:-(\d+)[:\.]?(\d+)?)?', subtitle)
    if match:
        start_chapter = int(match.group(1))
        start_verse = int(match.group(2))
        
        if match.group(3):  # Range exists
            if match.group(4):  # Different chapter
                end_chapter = int(match.group(3))
                end_verse = int(match.group(4))
            else:  # Same chapter
                end_chapter = start_chapter
                end_verse = int(match.group(3))
        else:
            end_chapter = start_chapter
            end_verse = start_verse
        
        return {
            'book': 'matthew',
            'start': {'chapter': start_chapter, 'verse': start_verse},
            'end': {'chapter': end_chapter, 'verse': end_verse},
            'display': subtitle
        }
    
    return None

def extract_scripture_refs_from_text(text):
    """Extract all scripture references from text."""
    refs = []
    
    # Pattern for biblical references
    patterns = [
        r'(\w+\.?)\s+(\d+)[:\.](\d+)(?:-(\d+))?',
        r'(\d\s+\w+\.?)\s+(\d+)[:\.](\d+)(?:-(\d+))?'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            book = normalize_book_name(match.group(1))
            if book:
                ref = {
                    'book': book,
                    'chapter': int(match.group(2)),
                    'verse': int(match.group(3))
                }
                if match.group(4):
                    ref['end_verse'] = int(match.group(4))
                refs.append(ref)
    
    return refs

def normalize_book_name(name):
    """Normalize book name to standard format."""
    name = name.lower().strip().replace('.', '')
    
    book_map = {
        'matt': 'matthew', 'matthew': 'matthew', 'mt': 'matthew',
        'mark': 'mark', 'mk': 'mark',
        'luke': 'luke', 'lk': 'luke',
        'john': 'john', 'jn': 'john',
        'acts': 'acts',
        'rom': 'romans', 'romans': 'romans',
        'cor': 'corinthians', '1 cor': '1_corinthians', '2 cor': '2_corinthians',
        'gal': 'galatians', 'galatians': 'galatians',
        'eph': 'ephesians', 'ephesians': 'ephesians',
        'phil': 'philippians', 'philippians': 'philippians',
        'col': 'colossians', 'colossians': 'colossians',
        'thess': 'thessalonians', '1 thess': '1_thessalonians', '2 thess': '2_thessalonians',
        'tim': 'timothy', '1 tim': '1_timothy', '2 tim': '2_timothy',
        'titus': 'titus',
        'philem': 'philemon', 'philemon': 'philemon',
        'heb': 'hebrews', 'hebrews': 'hebrews',
        'james': 'james', 'jas': 'james',
        'pet': 'peter', '1 pet': '1_peter', '2 pet': '2_peter',
        'jude': 'jude',
        'rev': 'revelation', 'revelation': 'revelation',
        # Old Testament
        'gen': 'genesis', 'genesis': 'genesis',
        'ex': 'exodus', 'exodus': 'exodus',
        'lev': 'leviticus', 'leviticus': 'leviticus',
        'num': 'numbers', 'numbers': 'numbers',
        'deut': 'deuteronomy', 'deuteronomy': 'deuteronomy',
        'isa': 'isaiah', 'isaiah': 'isaiah',
        'jer': 'jeremiah', 'jeremiah': 'jeremiah',
        'ps': 'psalms', 'psalm': 'psalms', 'psalms': 'psalms',
        'prov': 'proverbs', 'proverbs': 'proverbs'
    }
    
    return book_map.get(name)

def process_thml_file():
    """Process the ThML source file and generate all JSON files."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    print("Parsing ThML source file...")
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all homily boundaries
    print("Finding homily boundaries...")
    boundaries = extract_homily_boundaries(soup)
    print(f"Found {len(boundaries)} homilies")
    
    # Process each homily
    for homily_num in range(1, 91):
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract content and footnotes
        content_data, footnotes = extract_homily_content(soup, homily_num, boundaries)
        
        if content_data and content_data['paragraphs']:
            # Save content.json
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Generate metadata
            metadata = {
                'id': homily_num,
                'roman': to_roman(homily_num),
                'title': content_data['title'],
                'subtitle': content_data['subtitle'],
                'author': 'chrysostom',
                'author_full': 'John Chrysostom',
                'work': 'Homilies on Matthew',
                'scripture_reference': extract_scripture_reference(content_data['subtitle']),
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                'source_file': 'chrysostom_matthew_homilies.xml',
                'extraction_method': 'thml',
                'has_footnotes': len(footnotes) > 0,
                'footnotes': footnotes,
                'verified': True
            }
            
            with open(homily_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Generate scripture references
            scripture_refs = {}
            
            # From content
            for para in content_data['paragraphs']:
                refs = extract_scripture_refs_from_text(para)
                for ref in refs:
                    book = ref['book']
                    if book not in scripture_refs:
                        scripture_refs[book] = []
                    scripture_refs[book].append({
                        'chapter': ref['chapter'],
                        'verse': ref['verse'],
                        'end_verse': ref.get('end_verse')
                    })
            
            # From footnotes
            for fn_id, fn_text in footnotes.items():
                refs = extract_scripture_refs_from_text(fn_text)
                for ref in refs:
                    book = ref['book']
                    if book not in scripture_refs:
                        scripture_refs[book] = []
                    scripture_refs[book].append({
                        'chapter': ref['chapter'],
                        'verse': ref['verse'],
                        'end_verse': ref.get('end_verse'),
                        'source': f'footnote_{fn_id}'
                    })
            
            with open(homily_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
                json.dump(scripture_refs, f, indent=2, ensure_ascii=False)
            
            print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
        else:
            print(f"Homily {homily_num:3d}: No content found")
    
    # Generate coverage.json
    print("\nGenerating coverage.json...")
    coverage = {
        'commentary': 'chrysostom_matthew',
        'total_homilies': 90,
        'homilies': []
    }
    
    for homily_num in range(1, 91):
        metadata_file = content_dir / f'{homily_num:03d}' / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            scripture_ref = metadata.get('scripture_reference', {})
            if scripture_ref:
                coverage['homilies'].append({
                    'id': homily_num,
                    'roman': metadata['roman'],
                    'title': metadata['title'],
                    'start': scripture_ref.get('start', {'chapter': 1, 'verse': 1}),
                    'end': scripture_ref.get('end', {'chapter': 1, 'verse': 1})
                })
    
    with open(base_dir / 'coverage.json', 'w', encoding='utf-8') as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)
    
    # Generate verse_mapping.json
    print("Generating verse_mapping.json...")
    verse_map = {}
    
    for homily in coverage['homilies']:
        homily_id = homily['id']
        start_ch = homily['start']['chapter']
        start_v = homily['start']['verse']
        end_ch = homily['end']['chapter']
        end_v = homily['end']['verse']
        
        # Add verses covered
        if start_ch == end_ch:
            for v in range(start_v, end_v + 1):
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
        else:
            # Handle multi-chapter ranges
            for v in range(start_v, 100):  # First chapter
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
    
    with open(base_dir / 'verse_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2, ensure_ascii=False)
    
    print("\nAll JSON files generated successfully!")

def main():
    print("Complete Chrysostom Matthew JSON Generation")
    print("=" * 60)
    process_thml_file()

if __name__ == "__main__":
    main()
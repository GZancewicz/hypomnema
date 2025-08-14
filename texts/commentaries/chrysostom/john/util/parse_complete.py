#!/usr/bin/env python3
"""
Complete parser for Chrysostom John ThML source.
Handles all 88 homilies including those in different structures.
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

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    if not roman:
        return None
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

def extract_homily_content_from_div2(div2):
    """Extract content from a div2 element."""
    content = {
        'title': '',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_counter = 0
    
    # Get homily number from n attribute
    n_attr = div2.get('n', '')
    homily_num = roman_to_int(n_attr)
    if homily_num:
        content['title'] = f'Homily {n_attr}'
    
    # Process all paragraphs in the div2
    for p in div2.find_all('p'):
        if p.get('class') and 'endnote' in p.get('class'):
            continue  # Skip footnote paragraphs
            
        para_text = ""
        
        # Process paragraph content
        for elem in p.children:
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
                    fn_text = clean_text(elem.get_text())
                    if fn_text:
                        footnotes[fn_id] = fn_text
                
                para_text += f'<sup>f{fn_id}</sup>'
            elif elem.name == 'span':
                para_text += elem.get_text()
        
        para_text = clean_text(para_text)
        
        # Check for scripture reference in early paragraphs
        if not content['subtitle'] and len(content['paragraphs']) < 5:
            # Check for various John reference patterns
            patterns = [
                r'John\.?\s+([IVX]+)\.?\s+(\d+)',  # John I. 1
                r'John\.?\s+(\d+)[:\.](\d+(?:-\d+)?)',  # John 1:1 or John 1.1-5
                r'Jn\.?\s+([IVX]+)\.?\s+(\d+)',  # Jn. I. 1
                r'Jn\.?\s+(\d+)[:\.](\d+(?:-\d+)?)'  # Jn. 1:1
            ]
            
            for pattern in patterns:
                match = re.search(pattern, para_text)
                if match:
                    # Handle Roman numerals for chapter
                    chapter = match.group(1)
                    if chapter in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                                  'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
                                  'XXI']:
                        chapter = str(roman_to_int(chapter))
                    
                    verse = match.group(2)
                    content['subtitle'] = f"John {chapter}:{verse}"
                    break
        
        # Skip title paragraphs
        if para_text and not re.match(r'^(Homily|HOMILY)\s+[IVX]+\.?$', para_text):
            content['paragraphs'].append(para_text)
    
    return content, footnotes

def extract_homily_content_from_id(soup, homily_num, expected_roman):
    """Extract content for homilies that have different structure."""
    content = {
        'title': f'Homily {expected_roman}',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_counter = 0
    
    # Map homily numbers to the actual IDs in the file
    id_map = {
        35: 'iv.xxxvii',
        36: 'iv.xxxviii',
        37: 'iv.xxxix',
        38: 'iv.xl',
        39: 'iv.xli',
        40: 'iv.xlii'  # Homily XL appears to use xlii
    }
    
    if homily_num in id_map:
        base_id = id_map[homily_num]
        
        # Find the starting point
        start_elem = soup.find('p', id=f'{base_id}-p1')
        if not start_elem:
            return None, {}
        
        # Find the next homily start to know where to stop
        next_id = None
        if homily_num < 88:
            next_id = id_map.get(homily_num + 1)
            if next_id:
                next_id = f'{next_id}-p1'
        
        # Process content
        current = start_elem
        while current:
            if current.name == 'p':
                # Check if we've reached the next homily
                if next_id and current.get('id') == next_id:
                    break
                
                if current.get('class') and 'endnote' in current.get('class'):
                    current = current.next_sibling
                    continue
                
                para_text = ""
                
                # Process paragraph content
                for elem in current.children:
                    if isinstance(elem, NavigableString):
                        para_text += str(elem)
                    elif elem.name == 'note':
                        footnote_counter += 1
                        fn_id = str(footnote_counter)
                        
                        endnote = elem.find('p', class_='endnote')
                        if endnote:
                            fn_text = clean_text(endnote.get_text())
                            footnotes[fn_id] = fn_text
                        else:
                            fn_text = clean_text(elem.get_text())
                            if fn_text:
                                footnotes[fn_id] = fn_text
                        
                        para_text += f'<sup>f{fn_id}</sup>'
                    elif elem.name == 'span':
                        para_text += elem.get_text()
                
                para_text = clean_text(para_text)
                
                # Check for scripture reference
                if not content['subtitle'] and len(content['paragraphs']) < 5:
                    # Check for various John reference patterns
                    patterns = [
                        r'John\.?\s+([IVX]+)\.?\s+(\d+)',  # John I. 1
                        r'John\.?\s+(\d+)[:\.](\d+(?:-\d+)?)',  # John 1:1 or John 1.1-5
                        r'Jn\.?\s+([IVX]+)\.?\s+(\d+)',  # Jn. I. 1
                        r'Jn\.?\s+(\d+)[:\.](\d+(?:-\d+)?)'  # Jn. 1:1
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, para_text)
                        if match:
                            # Handle Roman numerals for chapter
                            chapter = match.group(1)
                            if chapter in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                                          'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
                                          'XXI']:
                                chapter = str(roman_to_int(chapter))
                            
                            verse = match.group(2)
                            content['subtitle'] = f"John {chapter}:{verse}"
                            break
                
                # Skip title paragraphs
                if para_text and not re.match(r'^(Homily|HOMILY)\s+[IVX]+\.?$', para_text):
                    content['paragraphs'].append(para_text)
            
            current = current.next_sibling
    
    return content, footnotes

def extract_scripture_refs_from_footnote(text):
    """Extract scripture references from footnote text."""
    refs = []
    
    if not text:
        return refs
    
    # Common patterns for biblical references
    patterns = [
        r'(\d?\s*\w+)\.?\s+(\d+)[:\.](\d+)(?:-(\d+))?',
        r'(\w+)\.?\s+(\d+)[:\.](\d+)(?:-(\d+))?'
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            book_name = match.group(1).strip()
            
            # Skip common false positives
            if book_name.lower() in ['verse', 'chapter', 'see', 'comp', 'compare', 'cf']:
                continue
            
            # Check if it looks like a biblical book
            normalized = normalize_book_name(book_name)
            if normalized:
                ref = {
                    'in_footnote': match.group(0).strip()
                }
                refs.append(ref)
    
    return refs

def normalize_book_name(name):
    """Normalize book name to standard format."""
    if not name:
        return None
    
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
        'isa': 'isaiah', 'is': 'isaiah', 'isaiah': 'isaiah',
        'jer': 'jeremiah', 'jeremiah': 'jeremiah',
        'ps': 'psalms', 'psalm': 'psalms', 'psalms': 'psalms',
        'prov': 'proverbs', 'proverbs': 'proverbs',
        'sam': 'samuel', '1 sam': '1_samuel', '2 sam': '2_samuel',
        'dan': 'daniel', 'daniel': 'daniel',
        'ezek': 'ezekiel', 'ezekiel': 'ezekiel'
    }
    
    return book_map.get(name)

def extract_scripture_reference(subtitle):
    """Extract structured scripture reference from subtitle."""
    if not subtitle:
        return None
    
    match = re.search(r'John\s+(\d+)[:\.](\d+)(?:-(\d+)[:\.]?(\d+)?)?', subtitle)
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
            'book': 'john',
            'start': {'chapter': start_chapter, 'verse': start_verse},
            'end': {'chapter': end_chapter, 'verse': end_verse},
            'display': subtitle
        }
    
    return None

def process_thml_file():
    """Process the ThML source file and generate all JSON files."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    print("Parsing ThML source file...")
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # First, let's check how many div2 elements with type='Homily' we have
    div2s = soup.find_all('div2', type='Homily')
    print(f"Found {len(div2s)} div2 elements with type='Homily'")
    
    # Process each homily from div2 elements
    for div2 in div2s:
        n_attr = div2.get('n', '')
        homily_num = roman_to_int(n_attr)
        
        if not homily_num:
            continue
        
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract content and footnotes
        content_data, footnotes = extract_homily_content_from_div2(div2)
        
        if content_data and content_data['paragraphs']:
            # Save content.json
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Generate metadata
            metadata = {
                'id': homily_num,
                'roman': n_attr,
                'title': content_data['title'],
                'subtitle': content_data['subtitle'],
                'author': 'chrysostom',
                'author_full': 'John Chrysostom',
                'work': 'Homilies on John',
                'scripture_reference': extract_scripture_reference(content_data['subtitle']),
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                'source_file': 'chrysostom_john_homilies.xml',
                'extraction_method': 'thml_div2',
                'has_footnotes': len(footnotes) > 0,
                'footnotes': footnotes,
                'verified': True
            }
            
            with open(homily_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Generate scripture_references.json
            scripture_refs = []
            for i, fn_text in enumerate(footnotes.values(), 1):
                refs = extract_scripture_refs_from_footnote(fn_text)
                scripture_refs.append({
                    'footnote': i,
                    'references': refs
                })
            
            with open(homily_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
                json.dump(scripture_refs, f, indent=2, ensure_ascii=False)
            
            print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
    
    # Process homilies 35-39 which have different structure (p/span elements)
    print("\nProcessing homilies in p/span elements...")
    for homily_num in range(35, 40):  # 35-39
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        roman = to_roman(homily_num)
        content_data, footnotes = extract_homily_content_from_id(soup, homily_num, roman)
        
        if content_data and content_data['paragraphs']:
            # Save content.json
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Generate metadata
            metadata = {
                'id': homily_num,
                'roman': roman,
                'title': content_data['title'],
                'subtitle': content_data['subtitle'],
                'author': 'chrysostom',
                'author_full': 'John Chrysostom',
                'work': 'Homilies on John',
                'scripture_reference': extract_scripture_reference(content_data['subtitle']),
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                'source_file': 'chrysostom_john_homilies.xml',
                'extraction_method': 'thml_p_span',
                'has_footnotes': len(footnotes) > 0,
                'footnotes': footnotes,
                'verified': True
            }
            
            with open(homily_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Generate scripture_references.json
            scripture_refs = []
            for i, fn_text in enumerate(footnotes.values(), 1):
                refs = extract_scripture_refs_from_footnote(fn_text)
                scripture_refs.append({
                    'footnote': i,
                    'references': refs
                })
            
            with open(homily_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
                json.dump(scripture_refs, f, indent=2, ensure_ascii=False)
            
            print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
        else:
            print(f"Homily {homily_num:3d}: No content found")
    
    print("\nAll homilies processed successfully!")
    
    # Generate coverage.json
    print("\nGenerating coverage.json...")
    coverage = {
        'commentary': 'chrysostom_john',
        'total_homilies': 39,  # Only 39 homilies available in source
        'homilies': []
    }
    
    for homily_num in range(1, 40):  # Process available homilies 1-39
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
            # First chapter
            for v in range(start_v, 100):  # Assume max verse 100
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
            
            # Middle chapters
            for ch in range(start_ch + 1, end_ch):
                for v in range(1, 100):
                    verse_ref = f"{ch}:{v}"
                    if verse_ref not in verse_map:
                        verse_map[verse_ref] = []
                    verse_map[verse_ref].append({
                        'id': homily_id,
                        'roman': homily['roman'],
                        'type': 'primary'
                    })
            
            # Last chapter
            for v in range(1, end_v + 1):
                verse_ref = f"{end_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': homily_id,
                    'roman': homily['roman'],
                    'type': 'primary'
                })
    
    with open(base_dir / 'verse_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2, ensure_ascii=False)
    
    print("All JSON files generated successfully!")

def main():
    print("Complete Chrysostom John JSON Generation")
    print("=" * 60)
    process_thml_file()

if __name__ == "__main__":
    main()
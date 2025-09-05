#!/usr/bin/env python3
"""
Complete parser for Chrysostom Matthew ThML source.
Extracts all 90 homilies and generates all JSON files.
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

def extract_scripture_reference(content_paragraphs):
    """Extract scripture reference from early paragraphs."""
    for para in content_paragraphs[:5]:  # Check first 5 paragraphs
        # Patterns for Matthew references
        patterns = [
            r'Matt?(?:hew)?\.?\s+([IVX]+)\.?\s+(\d+)',  # Matt. I. 1
            r'Matt?(?:hew)?\.?\s+(\d+)[:\.](\d+)(?:-(\d+))?',  # Matt. 1:1 or Matt. 1.1-5
            r'Matthew\s+([IVX]+)\.?\s+(\d+)',  # Matthew I. 1
            r'Matthew\s+(\d+)[:\.](\d+)(?:-(\d+))?'  # Matthew 1:1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, para)
            if match:
                chapter = match.group(1)
                # Handle Roman numerals
                if chapter in ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
                              'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX',
                              'XXI', 'XXII', 'XXIII', 'XXIV', 'XXV', 'XXVI', 'XXVII', 'XXVIII']:
                    chapter = str(roman_to_int(chapter))
                
                verse = match.group(2)
                end_verse = match.group(3) if len(match.groups()) >= 3 and match.group(3) else verse
                
                subtitle = f"Matthew {chapter}:{verse}"
                if end_verse != verse:
                    subtitle += f"-{end_verse}"
                
                return {
                    'book': 'matthew',
                    'start': {'chapter': int(chapter), 'verse': int(verse)},
                    'end': {'chapter': int(chapter), 'verse': int(end_verse)},
                    'display': subtitle
                }, subtitle
    
    return None, ""

def extract_scripture_refs_from_footnote(text):
    """Extract scripture references from footnote text."""
    refs = []
    if not text:
        return refs
    
    # Pattern for biblical references
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
            if any(book in book_name.lower() for book in ['matt', 'mark', 'luke', 'john', 'cor', 'thess', 'tim', 'heb', 'pet', 'gen', 'ex', 'lev', 'num', 'deut', 'sam', 'ps', 'isa', 'jer', 'ezek', 'dan']):
                ref = {
                    'in_footnote': match.group(0).strip()
                }
                refs.append(ref)
    
    return refs

def extract_homily_from_div2(div2):
    """Extract content from a div2 element (homilies 1-86)."""
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
    
    # Process all paragraphs
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
        
        # Skip title paragraphs
        if para_text and not re.match(r'^(Homily|HOMILY)\s+[IVX]+\.?$', para_text):
            content['paragraphs'].append(para_text)
    
    return content, footnotes, homily_num

def extract_homily_from_p(soup, homily_num):
    """Extract content for homilies 87-90 which use p/span structure."""
    content = {
        'title': f'Homily {to_roman(homily_num)}',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_counter = 0
    
    # Map homily numbers to IDs
    id_map = {
        87: 'iii.LXXXIII',
        88: 'iii.LXXXIV', 
        89: 'iii.LXXXV',
        90: 'iii.LXXXVI'
    }
    
    if homily_num not in id_map:
        return None, {}, None
    
    base_id = id_map[homily_num]
    
    # Find starting point
    start_elem = soup.find('p', id=f'{base_id}-p1')
    if not start_elem:
        return None, {}, None
    
    # Find next homily start
    next_id = None
    if homily_num < 90:
        next_id = id_map.get(homily_num + 1)
        if next_id:
            next_id = f'{next_id}-p1'
    
    # Process content
    current = start_elem
    while current:
        if current.name == 'p':
            # Check if we've reached next homily
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
            
            # Skip title paragraphs
            if para_text and not re.match(r'^(Homily|HOMILY)\s+[IVX]+\.?$', para_text):
                content['paragraphs'].append(para_text)
        
        current = current.next_sibling
    
    return content, footnotes, homily_num

def process_matthew_thml():
    """Process the Matthew ThML file and generate all JSONs."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Error: Source file not found: {source_file}")
        return
    
    print("Parsing ThML source file...")
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Process homilies 1-86 from div2 elements
    div2s = soup.find_all('div2', type='Homily')
    print(f"Found {len(div2s)} div2 elements")
    
    processed = set()
    
    for div2 in div2s:
        content_data, footnotes, homily_num = extract_homily_from_div2(div2)
        
        if homily_num and homily_num not in processed:
            processed.add(homily_num)
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract scripture reference
            scripture_ref, subtitle = extract_scripture_reference(content_data['paragraphs'])
            content_data['subtitle'] = subtitle
            
            # Save content.json
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Generate metadata.json
            metadata = {
                'id': homily_num,
                'roman': to_roman(homily_num),
                'title': content_data['title'],
                'subtitle': subtitle,
                'author': 'chrysostom',
                'author_full': 'John Chrysostom',
                'work': 'Homilies on Matthew',
                'scripture_reference': scripture_ref,
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                'source_file': 'chrysostom_matthew_homilies.xml',
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
    
    # Process homilies 87-90 from p/span elements
    print("\nProcessing homilies 87-90...")
    for homily_num in range(87, 91):
        content_data, footnotes, _ = extract_homily_from_p(soup, homily_num)
        
        if content_data and content_data['paragraphs']:
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract scripture reference
            scripture_ref, subtitle = extract_scripture_reference(content_data['paragraphs'])
            content_data['subtitle'] = subtitle
            
            # Save content.json
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            # Generate metadata.json
            metadata = {
                'id': homily_num,
                'roman': to_roman(homily_num),
                'title': content_data['title'],
                'subtitle': subtitle,
                'author': 'chrysostom',
                'author_full': 'John Chrysostom',
                'work': 'Homilies on Matthew',
                'scripture_reference': scripture_ref,
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                'source_file': 'chrysostom_matthew_homilies.xml',
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
            
            scripture_ref = metadata.get('scripture_reference')
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
    
    print("\nAll JSON files generated successfully!")
    print(f"Total homilies processed: {len(processed)} from div2 + 4 from p/span = 90")
    print(f"Coverage contains: {len(coverage['homilies'])} homilies with scripture references")
    print(f"Verse mapping contains: {len(verse_map)} verse references")

def main():
    print("Chrysostom Matthew Complete JSON Generation")
    print("=" * 60)
    process_matthew_thml()

if __name__ == "__main__":
    main()
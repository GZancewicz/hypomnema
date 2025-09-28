#!/usr/bin/env python3
"""
Complete parser for Chrysostom John ThML source.
Extracts all 88 homilies and generates all JSON files.
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

def extract_scripture_reference(div2_element):
    """Extract scripture reference from div2 title attribute."""
    title = div2_element.get('title', '')
    
    # Common pattern: "John 1.1" or "John 1.1,2" or "John 1.1—3"
    patterns = [
        r'John\s+(\d+)[:\.](\d+)(?:[-–—]+(\d+))?(?:\s*,\s*(\d+))?',  # John 1:1-3 or John 1.1,2
        r'John\s+(\d+)[:\.](\d+)(?:[-–—]+(\d+)[:\.](\d+))?',  # John 1:1-2:3
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            chapter = int(match.group(1))
            verse = int(match.group(2))
            
            # Check for end verse in same chapter or end verse after comma
            if match.group(3) and match.group(3).isdigit():
                end_verse = int(match.group(3))
                end_chapter = chapter
            elif match.group(4) and match.group(4).isdigit():
                end_verse = int(match.group(4))
                end_chapter = chapter
            else:
                end_verse = verse
                end_chapter = chapter
            
            subtitle = f"John {chapter}:{verse}"
            if end_chapter == chapter and end_verse != verse:
                subtitle += f"-{end_verse}"
            elif end_chapter != chapter:
                subtitle += f"-{end_chapter}:{end_verse}"
            
            return {
                'book': 'john',
                'start': {'chapter': chapter, 'verse': verse},
                'end': {'chapter': end_chapter, 'verse': end_verse},
                'display': subtitle
            }, subtitle
    
    # If no match, return empty
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

def process_john_thml():
    """Process the John ThML file and generate all JSONs."""
    base_dir = Path(__file__).parent.parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Error: Source file not found: {source_file}")
        return
    
    print("Parsing ThML source file...")
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Process homilies from div2 elements - only those with John in title
    all_div2s = soup.find_all('div2', type='Homily')
    div2s = [d for d in all_div2s if d.get('title', '').startswith('John')]
    print(f"Found {len(div2s)} John homilies from {len(all_div2s)} total div2 elements")
    
    processed = set()
    homily_counter = 0
    
    for div2 in div2s:
        content_data, footnotes, _ = extract_homily_from_div2(div2)
        homily_counter += 1
        homily_num = homily_counter
        
        if homily_num <= 88:  # John has 88 homilies
            processed.add(homily_num)
            content_data['title'] = f'Homily {to_roman(homily_num)}'
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract scripture reference
            scripture_ref, subtitle = extract_scripture_reference(div2)
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
                'work': 'Homilies on John',
                'scripture_reference': scripture_ref,
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
    
    # Generate coverage.json
    print("\nGenerating coverage.json...")
    coverage = {
        'commentary': 'chrysostom_john',
        'total_homilies': 88,
        'homilies': []
    }
    
    for homily_num in range(1, 89):
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
    print(f"Total homilies processed: {len(processed)}")
    print(f"Coverage contains: {len(coverage['homilies'])} homilies with scripture references")
    print(f"Verse mapping contains: {len(verse_map)} verse references")

def main():
    print("Chrysostom John Complete JSON Generation")
    print("=" * 60)
    process_john_thml()

if __name__ == "__main__":
    main()
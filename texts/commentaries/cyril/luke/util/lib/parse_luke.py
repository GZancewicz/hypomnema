#!/usr/bin/env python3
"""
Complete parser for Cyril Luke HTML sources.
Extracts all sermons and generates all JSON files.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
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

def extract_scripture_reference(sermon_header):
    """Extract scripture reference from sermon header."""
    # Patterns for Luke references
    patterns = [
        r'S\.\s+Luke\s+([ivxlc]+)[,\.\s]+(\d+)(?:\s*[-–]\s*(\d+))?',  # S. Luke i. 26-38
        r'Luke\s+([ivxlc]+)[,\.\s]+(\d+)(?:\s*[-–]\s*(\d+))?',  # Luke xii. 16-21
        r'From\s+the\s+Gospel\s+of\s+Luke[,\s]+ch\.\s*([ivxlc]+)',  # From the Gospel of Luke, ch. xi
        r'Luke\s+([ivxlc]+)',  # Luke xi
    ]
    
    for pattern in patterns:
        match = re.search(pattern, sermon_header, re.IGNORECASE)
        if match:
            chapter_str = match.group(1).lower()
            # Convert Roman to int
            chapter_val = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100}
            chapter = 0
            prev = 0
            for char in reversed(chapter_str):
                if char in chapter_val:
                    val = chapter_val[char]
                    if val < prev:
                        chapter -= val
                    else:
                        chapter += val
                    prev = val
            
            verse = int(match.group(2)) if len(match.groups()) >= 2 and match.group(2) else 1
            end_verse = int(match.group(3)) if len(match.groups()) >= 3 and match.group(3) else verse
            
            subtitle = f"Luke {chapter}:{verse}"
            if end_verse != verse:
                subtitle += f"-{end_verse}"
            
            return {
                'book': 'luke',
                'start': {'chapter': chapter, 'verse': verse},
                'end': {'chapter': chapter, 'verse': end_verse},
                'display': subtitle
            }, subtitle
    
    return None, ""

def extract_sermon_from_html(file_path, sermon_num):
    """Extract sermon content from HTML file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find sermon header - Look for h3 elements with sermon header text
    sermon_start = None
    sermon_header = ""
    scripture_text = ""
    
    # Convert number to ordinal - extend to cover all sermons
    ordinals = {
        1: "First", 2: "Second", 3: "Third", 4: "Fourth", 5: "Fifth",
        6: "Sixth", 7: "Seventh", 8: "Eighth", 9: "Ninth", 10: "Tenth",
        11: "Eleventh", 12: "Twelfth", 13: "Thirteenth", 14: "Fourteenth", 15: "Fifteenth",
        16: "Sixteenth", 17: "Seventeenth", 18: "Eighteenth", 19: "Nineteenth", 20: "Twentieth"
    }
    # For numbers > 20, just use the number
    for i in range(21, 157):
        ordinals[i] = str(i)
    
    # Search for the sermon header
    ordinal = ordinals.get(sermon_num % 100, str(sermon_num))
    patterns = [
        f'Sermon the {ordinal}',
        f'Sermon {sermon_num}',
        f'SERMON {sermon_num}'
    ]
    
    for pattern in patterns:
        for elem in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
            parent = elem.parent
            # Check if parent is i, b, or similar inside h3/h2
            while parent and parent.name not in ['h3', 'h2', 'body', None]:
                if parent.name in ['h3', 'h2']:
                    break
                parent = parent.parent
            
            if parent and parent.name in ['h3', 'h2']:
                sermon_start = parent
                sermon_header = elem.strip()
                # Look for scripture reference after header
                next_elem = parent.find_next_sibling()
                # Skip "From the Syriac" line
                if next_elem and "From the Syriac" in next_elem.get_text():
                    next_elem = next_elem.find_next_sibling()
                
                while next_elem and next_elem.name in ['p', 'blockquote']:
                    text = next_elem.get_text().strip()
                    if re.match(r'Luke\s+[ivxlc]+', text, re.IGNORECASE):
                        scripture_text = text
                        break
                    next_elem = next_elem.find_next_sibling()
                break
        if sermon_start:
            break
    
    if not sermon_start:
        return None, None, None
    
    # Extract scripture reference
    scripture_ref, subtitle = extract_scripture_reference(scripture_text if scripture_text else sermon_header)
    
    # Collect content paragraphs
    paragraphs = []
    footnotes = {}
    footnote_counter = 0
    
    # Start from after the sermon header
    current = sermon_start.find_next_sibling()
    
    # Skip "From the Syriac" line and find scripture reference
    found_scripture = False
    while current and not found_scripture:
        if current.name == 'blockquote':
            # Check if this blockquote contains Luke reference
            blockquote_text = current.get_text().strip()
            if re.match(r'Luke\s+[ivxlc]+', blockquote_text, re.IGNORECASE):
                if not scripture_text:
                    scripture_text = blockquote_text
                found_scripture = True
                current = current.find_next_sibling()
                break
        elif current.name == 'p':
            text = current.get_text().strip()
            if "From the Syriac" in text or "MS." in text:
                # Skip metadata lines
                current = current.find_next_sibling()
                continue
            elif re.match(r'Luke\s+[ivxlc]+', text, re.IGNORECASE):
                if not scripture_text:
                    scripture_text = text
                found_scripture = True
                current = current.find_next_sibling()
                break
            else:
                # This is content, start collecting
                break
        current = current.find_next_sibling()
    
    # Extract scripture reference if we found one
    if scripture_text:
        scripture_ref, subtitle = extract_scripture_reference(scripture_text)
    else:
        scripture_ref, subtitle = None, ""
    
    # Collect paragraphs until next sermon
    while current:
        # Stop at next sermon header
        if current.name in ['h3', 'h2'] and re.search(r'sermon', current.get_text(), re.IGNORECASE):
            break
        
        if current.name == 'p':
            para_text = ""
            for elem in current.children:
                if isinstance(elem, str):
                    para_text += elem
                elif elem.name == 'sup':
                    # This is a footnote marker
                    footnote_counter += 1
                    fn_id = str(footnote_counter)
                    para_text += f'<sup>f{fn_id}</sup>'
                else:
                    para_text += elem.get_text()
            
            para_text = clean_text(para_text)
            # Skip navigation and reference paragraphs
            if para_text and not re.match(r'^(sermon|from the syriac|luke\s+[ivxlc]+)', para_text, re.IGNORECASE):
                paragraphs.append(para_text)
        
        current = current.find_next_sibling()
    
    content = {
        'title': f'Sermon {to_roman(sermon_num)}',
        'subtitle': subtitle,
        'paragraphs': paragraphs
    }
    
    return content, footnotes, scripture_ref

def process_cyril_luke():
    """Process all Cyril Luke HTML files and generate JSONs."""
    base_dir = Path(__file__).parent.parent.parent
    source_dir = base_dir / 'source'
    content_dir = base_dir / 'content'
    
    # HTML files and their sermon ranges
    file_ranges = [
        ('cyril_on_luke_01_sermons_01_11.htm', 1, 11),
        ('cyril_on_luke_02_sermons_12_25.htm', 12, 25),
        ('cyril_on_luke_03_sermons_27_38.htm', 27, 38),
        ('cyril_on_luke_04_sermons_39_46.htm', 39, 46),
        ('cyril_on_luke_05_sermons_47_56.htm', 47, 56),
        ('cyril_on_luke_06_sermons_57_65.htm', 57, 65),
        ('cyril_on_luke_07_sermons_66_80.htm', 66, 80),
        ('cyril_on_luke_08_sermons_81_88.htm', 81, 88),
        ('cyril_on_luke_09_sermons_89_98.htm', 89, 98),
        ('cyril_on_luke_10_sermons_99_109.htm', 99, 109),
        ('cyril_on_luke_11_sermons_110_123.htm', 110, 123),
        ('cyril_on_luke_12_sermons_124_134.htm', 124, 134),
        ('cyril_on_luke_13_sermons_135_145.htm', 135, 145),
        ('cyril_on_luke_14_sermons_146_156.htm', 146, 156),
    ]
    
    print("Processing Cyril Luke sermons...")
    processed = 0
    
    for file_name, start_num, end_num in file_ranges:
        file_path = source_dir / file_name
        if not file_path.exists():
            print(f"Warning: {file_name} not found")
            continue
        
        print(f"\nProcessing {file_name}...")
        
        for sermon_num in range(start_num, end_num + 1):
            # Skip missing sermons (26, 154-156)
            if sermon_num in [26, 154, 155, 156]:
                continue
            
            content_data, footnotes, scripture_ref = extract_sermon_from_html(file_path, sermon_num)
            
            if content_data:
                if not content_data.get('paragraphs'):
                    print(f"Sermon {sermon_num:3d}: Found header but no paragraphs")
                else:
                    sermon_dir = content_dir / f'{sermon_num:03d}'
                    sermon_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save content.json
                    with open(sermon_dir / 'content.json', 'w', encoding='utf-8') as f:
                        json.dump(content_data, f, indent=2, ensure_ascii=False)
                    
                    # Generate metadata.json
                    metadata = {
                        'id': sermon_num,
                        'roman': to_roman(sermon_num),
                        'title': content_data['title'],
                        'subtitle': content_data['subtitle'],
                        'author': 'cyril',
                        'author_full': 'Cyril of Alexandria',
                        'work': 'Commentary on Luke',
                        'scripture_reference': scripture_ref,
                        'themes': [],
                        'date_delivered': None,
                        'word_count': sum(len(p.split()) for p in content_data['paragraphs']),
                        'excerpt': content_data['paragraphs'][0][:200] + '...' if content_data['paragraphs'] else '',
                        'source_file': file_name,
                        'extraction_method': 'html_parse',
                        'has_footnotes': len(footnotes) > 0,
                        'footnotes': footnotes,
                        'verified': True
                    }
                    
                    with open(sermon_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2, ensure_ascii=False)
                    
                    # Generate scripture_references.json
                    with open(sermon_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
                        json.dump([], f, indent=2, ensure_ascii=False)
                    
                    processed += 1
                    print(f"Sermon {sermon_num:3d}: {len(content_data['paragraphs'])} paragraphs")
    
    # Generate coverage.json
    print("\nGenerating coverage.json...")
    coverage = {
        'commentary': 'cyril_luke',
        'total_sermons': 153,  # 156 minus missing 26, 154-156
        'sermons': []
    }
    
    for sermon_num in range(1, 157):
        if sermon_num in [26, 154, 155, 156]:
            continue
        
        metadata_file = content_dir / f'{sermon_num:03d}' / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            scripture_ref = metadata.get('scripture_reference')
            if scripture_ref:
                coverage['sermons'].append({
                    'id': sermon_num,
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
    
    for sermon in coverage['sermons']:
        sermon_id = sermon['id']
        start_ch = sermon['start']['chapter']
        start_v = sermon['start']['verse']
        end_ch = sermon['end']['chapter']
        end_v = sermon['end']['verse']
        
        # Add verses covered
        if start_ch == end_ch:
            for v in range(start_v, end_v + 1):
                verse_ref = f"{start_ch}:{v}"
                if verse_ref not in verse_map:
                    verse_map[verse_ref] = []
                verse_map[verse_ref].append({
                    'id': sermon_id,
                    'roman': sermon['roman'],
                    'type': 'primary'
                })
    
    with open(base_dir / 'verse_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2, ensure_ascii=False)
    
    print("\nAll JSON files generated successfully!")
    print(f"Total sermons processed: {processed}")
    print(f"Coverage contains: {len(coverage['sermons'])} sermons with scripture references")
    print(f"Verse mapping contains: {len(verse_map)} verse references")

def main():
    print("Cyril Luke Complete JSON Generation")
    print("=" * 60)
    process_cyril_luke()

if __name__ == "__main__":
    main()
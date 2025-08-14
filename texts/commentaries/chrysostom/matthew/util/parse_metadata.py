#!/usr/bin/env python3
"""
Parse Chrysostom Matthew homilies and extract metadata.
Generates/updates metadata.json files for each homily.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def clean_text(text):
    """Clean text for metadata."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_scripture_reference(homily_elem, homily_num):
    """Extract scripture reference from homily."""
    # Try to find scripture reference in subtitle or specific elements
    subtitle = homily_elem.find('.//subtitle')
    if subtitle is not None:
        subtitle_text = clean_text(''.join(subtitle.itertext()))
        # Parse Matthew references
        match = re.search(r'Matt?(?:hew)?\.?\s*(\d+)[:\.](\d+)(?:\s*-\s*(\d+)[:\.](\d+))?', subtitle_text, re.I)
        if match:
            start_chapter = int(match.group(1))
            start_verse = int(match.group(2))
            if match.group(3):
                end_chapter = int(match.group(3))
                end_verse = int(match.group(4))
            else:
                end_chapter = start_chapter
                end_verse = start_verse
            
            return {
                'book': 'matthew',
                'start': {'chapter': start_chapter, 'verse': start_verse},
                'end': {'chapter': end_chapter, 'verse': end_verse},
                'display': f"Matthew {start_chapter}:{start_verse}" + 
                          (f"-{end_chapter}:{end_verse}" if (end_chapter != start_chapter or end_verse != start_verse) else "")
            }
    
    # Default reference based on homily coverage patterns
    return get_default_reference(homily_num)

def get_default_reference(homily_num):
    """Get default scripture reference based on known coverage."""
    # This is a simplified mapping - should be replaced with actual coverage data
    coverage_map = {
        1: {'start': {'chapter': 1, 'verse': 1}, 'end': {'chapter': 1, 'verse': 17}},
        2: {'start': {'chapter': 1, 'verse': 17}, 'end': {'chapter': 1, 'verse': 25}},
        # Add more mappings based on actual coverage
    }
    
    if homily_num in coverage_map:
        ref = coverage_map[homily_num]
        return {
            'book': 'matthew',
            'start': ref['start'],
            'end': ref['end'],
            'display': f"Matthew {ref['start']['chapter']}:{ref['start']['verse']}-{ref['end']['chapter']}:{ref['end']['verse']}"
        }
    
    return {
        'book': 'matthew',
        'start': {'chapter': 1, 'verse': 1},
        'end': {'chapter': 1, 'verse': 1},
        'display': 'Matthew 1:1'
    }

def extract_themes(homily_elem):
    """Extract themes from homily content."""
    themes = []
    # Look for theme indicators in the text
    text = ' '.join(homily_elem.itertext()).lower()
    
    # Common themes in Chrysostom's homilies
    theme_keywords = {
        'incarnation': ['incarnation', 'made flesh', 'became man'],
        'trinity': ['trinity', 'three persons', 'father son spirit'],
        'virtue': ['virtue', 'virtuous', 'moral excellence'],
        'prayer': ['prayer', 'pray', 'supplication'],
        'repentance': ['repent', 'repentance', 'contrition'],
        'charity': ['charity', 'almsgiving', 'love of neighbor'],
        'humility': ['humility', 'humble', 'lowliness'],
        'faith': ['faith', 'belief', 'trust in god'],
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in text for keyword in keywords):
            themes.append(theme)
    
    return themes[:5]  # Limit to 5 themes

def calculate_word_count(homily_elem):
    """Calculate word count of homily."""
    text = ' '.join(homily_elem.itertext())
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    return len(words)

def generate_excerpt(homily_elem, max_length=200):
    """Generate excerpt from first paragraph."""
    for para in homily_elem.findall('.//p'):
        text = clean_text(''.join(para.itertext()))
        if text and len(text) > 50:  # Skip very short paragraphs
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + '...'
            return text
    return ""

def parse_homily_metadata(homily_elem, homily_num):
    """Extract metadata from a homily element."""
    metadata = {
        'id': homily_num,
        'roman': to_roman(homily_num),
        'title': f'Homily {to_roman(homily_num)}',
        'subtitle': '',
        'author': 'chrysostom',
        'author_full': 'John Chrysostom',
        'work': 'Homilies on Matthew',
        'scripture_reference': extract_scripture_reference(homily_elem, homily_num),
        'themes': extract_themes(homily_elem),
        'date_delivered': None,
        'word_count': calculate_word_count(homily_elem),
        'excerpt': generate_excerpt(homily_elem),
        'source_file': 'chrysostom_matthew_homilies.xml',
        'extraction_method': 'xml',
        'has_footnotes': False,
        'footnotes': {},
        'verified': False
    }
    
    # Extract title
    title_elem = homily_elem.find('.//title')
    if title_elem is not None:
        metadata['title'] = clean_text(''.join(title_elem.itertext()))
    
    # Extract subtitle
    subtitle_elem = homily_elem.find('.//subtitle')
    if subtitle_elem is not None:
        metadata['subtitle'] = clean_text(''.join(subtitle_elem.itertext()))
    
    return metadata

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

def process_xml_source():
    """Process the XML source file and extract metadata."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    # Parse XML
    try:
        tree = ET.parse(source_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return
    
    # Process each homily
    homilies_processed = 0
    
    for homily_num in range(1, 91):  # Matthew has 90 homilies
        # Try different XPath patterns
        homily = root.find(f".//homily[@number='{homily_num}']")
        if homily is None:
            homily = root.find(f".//div[@id='homily{homily_num}']")
        if homily is None:
            homily = root.find(f".//div[@class='homily'][{homily_num}]")
        
        if homily is None:
            print(f"Homily {homily_num} not found in source")
            continue
        
        # Parse metadata
        metadata = parse_homily_metadata(homily, homily_num)
        
        # Create directory for this homily
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if metadata already exists and preserve footnotes
        metadata_file = homily_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            # Preserve footnotes and verification status
            if 'footnotes' in existing:
                metadata['footnotes'] = existing['footnotes']
                metadata['has_footnotes'] = len(existing['footnotes']) > 0
            if 'verified' in existing:
                metadata['verified'] = existing['verified']
        
        # Save metadata.json
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        homilies_processed += 1
        print(f"Homily {homily_num:3d}: Metadata generated")
    
    print(f"\nTotal homilies processed: {homilies_processed}")

def main():
    print("Parsing Chrysostom Matthew metadata...")
    print("-" * 50)
    process_xml_source()

if __name__ == "__main__":
    main()
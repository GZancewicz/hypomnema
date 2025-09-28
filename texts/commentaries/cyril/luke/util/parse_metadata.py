#!/usr/bin/env python3
"""
Parse Cyril Luke sermons and extract metadata.
Generates/updates metadata.json files for each sermon.
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

def extract_scripture_reference(sermon_elem, sermon_num):
    """Extract scripture reference from sermon."""
    # Try to find scripture reference in subtitle or specific elements
    subtitle = sermon_elem.find('.//subtitle')
    if subtitle is not None:
        subtitle_text = clean_text(''.join(subtitle.itertext()))
        # Parse Luke references
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
                'book': 'luke',
                'start': {'chapter': start_chapter, 'verse': start_verse},
                'end': {'chapter': end_chapter, 'verse': end_verse},
                'display': f"Luke {start_chapter}:{start_verse}" + 
                          (f"-{end_chapter}:{end_verse}" if (end_chapter != start_chapter or end_verse != start_verse) else "")
            }
    
    # Default reference based on sermon coverage patterns
    return get_default_reference(sermon_num)

def get_default_reference(sermon_num):
    """Get default scripture reference based on known coverage."""
    # This is a simplified mapping - should be replaced with actual coverage data
    coverage_map = {
        1: {'start': {'chapter': 1, 'verse': 1}, 'end': {'chapter': 1, 'verse': 17}},
        2: {'start': {'chapter': 1, 'verse': 17}, 'end': {'chapter': 1, 'verse': 25}},
        # Add more mappings based on actual coverage
    }
    
    if sermon_num in coverage_map:
        ref = coverage_map[sermon_num]
        return {
            'book': 'luke',
            'start': ref['start'],
            'end': ref['end'],
            'display': f"Luke {ref['start']['chapter']}:{ref['start']['verse']}-{ref['end']['chapter']}:{ref['end']['verse']}"
        }
    
    return {
        'book': 'luke',
        'start': {'chapter': 1, 'verse': 1},
        'end': {'chapter': 1, 'verse': 1},
        'display': 'Luke 1:1'
    }

def extract_themes(sermon_elem):
    """Extract themes from sermon content."""
    themes = []
    # Look for theme indicators in the text
    text = ' '.join(sermon_elem.itertext()).lower()
    
    # Common themes in Cyril's sermons
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

def calculate_word_count(sermon_elem):
    """Calculate word count of sermon."""
    text = ' '.join(sermon_elem.itertext())
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    return len(words)

def generate_excerpt(sermon_elem, max_length=200):
    """Generate excerpt from first paragraph."""
    for para in sermon_elem.findall('.//p'):
        text = clean_text(''.join(para.itertext()))
        if text and len(text) > 50:  # Skip very short paragraphs
            if len(text) > max_length:
                text = text[:max_length].rsplit(' ', 1)[0] + '...'
            return text
    return ""

def parse_sermon_metadata(sermon_elem, sermon_num):
    """Extract metadata from a sermon element."""
    metadata = {
        'id': sermon_num,
        'roman': to_roman(sermon_num),
        'title': f'Sermon {to_roman(sermon_num)}',
        'subtitle': '',
        'author': 'cyril',
        'author_full': 'John Cyril',
        'work': 'Sermons on Luke',
        'scripture_reference': extract_scripture_reference(sermon_elem, sermon_num),
        'themes': extract_themes(sermon_elem),
        'date_delivered': None,
        'word_count': calculate_word_count(sermon_elem),
        'excerpt': generate_excerpt(sermon_elem),
        'source_file': 'cyril_luke_sermons.xml',
        'extraction_method': 'xml',
        'has_footnotes': False,
        'footnotes': {},
        'verified': False
    }
    
    # Extract title
    title_elem = sermon_elem.find('.//title')
    if title_elem is not None:
        metadata['title'] = clean_text(''.join(title_elem.itertext()))
    
    # Extract subtitle
    subtitle_elem = sermon_elem.find('.//subtitle')
    if subtitle_elem is not None:
        metadata['subtitle'] = clean_text(''.join(subtitle_elem.itertext()))
    
    return metadata

def to_roman(num):
    """Convert number to Roman numeral."""
    values = [
        (100, 'C'), (153, 'XC'), (50, 'L'), (40, 'XL'),
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
    source_file = base_dir / 'source' / 'cyril_luke_sermons.xml'
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
    
    # Process each sermon
    sermons_processed = 0
    
    for sermon_num in range(1, 154):  # Luke has 153 sermons
        # Try different XPath patterns
        sermon = root.find(f".//sermon[@number='{sermon_num}']")
        if sermon is None:
            sermon = root.find(f".//div[@id='sermon{sermon_num}']")
        if sermon is None:
            sermon = root.find(f".//div[@class='sermon'][{sermon_num}]")
        
        if sermon is None:
            print(f"Sermon {sermon_num} not found in source")
            continue
        
        # Parse metadata
        metadata = parse_sermon_metadata(sermon, sermon_num)
        
        # Create directory for this sermon
        sermon_dir = content_dir / f'{sermon_num:03d}'
        sermon_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if metadata already exists and preserve footnotes
        metadata_file = sermon_dir / 'metadata.json'
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
        
        sermons_processed += 1
        print(f"Sermon {sermon_num:3d}: Metadata generated")
    
    print(f"\nTotal sermons processed: {sermons_processed}")

def main():
    print("Parsing Cyril Luke metadata...")
    print("-" * 50)
    process_xml_source()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Parse metadata from Chrysostom Matthew ThML source.
Generates metadata.json for each homily with scripture references and footnotes.
"""

import os
import sys
import json
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from parse_matthew import extract_homily_from_div2, extract_homily_from_p, extract_scripture_reference, to_roman
from bs4 import BeautifulSoup

def process_metadata():
    """Extract metadata for all 90 Matthew homilies."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    content_dir = base_dir / 'content'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Process homilies 1-86 from div2 elements
    div2s = soup.find_all('div2', type='Homily')
    for div2 in div2s:
        content_data, footnotes, homily_num = extract_homily_from_div2(div2)
        if homily_num:
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            scripture_ref, subtitle = extract_scripture_reference(content_data['paragraphs'])
            
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
            
            print(f"Homily {homily_num:3d}: {len(footnotes)} footnotes")
    
    # Process homilies 87-90 from p/span elements
    for homily_num in range(87, 91):
        content_data, footnotes, _ = extract_homily_from_p(soup, homily_num)
        if content_data and content_data['paragraphs']:
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            scripture_ref, subtitle = extract_scripture_reference(content_data['paragraphs'])
            
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
            
            print(f"Homily {homily_num:3d}: {len(footnotes)} footnotes")

def main():
    print("Parsing Chrysostom Matthew Metadata")
    print("=" * 60)
    process_metadata()
    print("\nMetadata parsing complete!")

if __name__ == "__main__":
    main()
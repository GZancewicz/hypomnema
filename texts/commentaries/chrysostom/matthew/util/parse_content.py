#!/usr/bin/env python3
"""
Parse content from Chrysostom Matthew ThML source.
Generates content.json for each homily with footnote markers.
"""

import os
import sys
import json
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from parse_matthew import extract_homily_from_div2, extract_homily_from_p
from bs4 import BeautifulSoup

def process_content():
    """Extract content for all 90 Matthew homilies."""
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
            
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs")
    
    # Process homilies 87-90 from p/span elements
    for homily_num in range(87, 91):
        content_data, footnotes, _ = extract_homily_from_p(soup, homily_num)
        if content_data and content_data['paragraphs']:
            homily_dir = content_dir / f'{homily_num:03d}'
            homily_dir.mkdir(parents=True, exist_ok=True)
            
            with open(homily_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs")

def main():
    print("Parsing Chrysostom Matthew Content")
    print("=" * 60)
    process_content()
    print("\nContent parsing complete!")

if __name__ == "__main__":
    main()
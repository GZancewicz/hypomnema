#!/usr/bin/env python3
"""
Simple parser for Cyril Luke HTML sources.
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

def process_all_files():
    """Process all Cyril Luke HTML files."""
    base_dir = Path(__file__).parent.parent.parent
    source_dir = base_dir / 'source'
    content_dir = base_dir / 'content'
    
    # Manually map sermons to their files and actual text patterns
    sermon_map = {
        1: ('cyril_on_luke_01_sermons_01_11.htm', 'Sermon the First', 'Luke 2:1-7'),
        2: ('cyril_on_luke_01_sermons_01_11.htm', 'Sermon the Second', 'Luke 2:8-18'),
        3: ('cyril_on_luke_01_sermons_01_11.htm', 'Sermon the Third', 'Luke 2:15-20'),
        # Add more as needed
    }
    
    for sermon_num, (file_name, pattern, scripture) in sermon_map.items():
        file_path = source_dir / file_name
        if not file_path.exists():
            continue
        
        print(f"Processing Sermon {sermon_num}...")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the sermon header
        sermon_start = None
        for elem in soup.find_all(string=re.compile(pattern, re.IGNORECASE)):
            parent = elem.parent
            while parent and parent.name not in ['h3', 'h2', 'body']:
                parent = parent.parent
            if parent and parent.name in ['h3', 'h2']:
                sermon_start = parent
                break
        
        if not sermon_start:
            print(f"  Sermon {sermon_num} header not found")
            continue
        
        # Collect all p tags after header until next sermon
        paragraphs = []
        current = sermon_start.find_next_sibling()
        
        while current:
            if current.name in ['h3', 'h2'] and 'sermon' in current.get_text().lower():
                break
            
            if current.name == 'p':
                text = clean_text(current.get_text())
                # Skip metadata and scripture reference lines
                if text and not any(skip in text.lower() for skip in 
                    ['from the syriac', 'ms.', 'luke ii.', 'luke iii.', 'luke iv.']):
                    paragraphs.append(text)
            
            current = current.find_next_sibling()
        
        if paragraphs:
            sermon_dir = content_dir / f'{sermon_num:03d}'
            sermon_dir.mkdir(parents=True, exist_ok=True)
            
            # Parse scripture reference
            chapter_match = re.search(r'(\d+):(\d+)', scripture)
            if chapter_match:
                chapter = int(chapter_match.group(1))
                verse = int(chapter_match.group(2))
                scripture_ref = {
                    'book': 'luke',
                    'start': {'chapter': chapter, 'verse': verse},
                    'end': {'chapter': chapter, 'verse': verse},
                    'display': scripture
                }
            else:
                scripture_ref = None
            
            content_data = {
                'title': f'Sermon {to_roman(sermon_num)}',
                'subtitle': scripture,
                'paragraphs': paragraphs
            }
            
            with open(sermon_dir / 'content.json', 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
            
            metadata = {
                'id': sermon_num,
                'roman': to_roman(sermon_num),
                'title': f'Sermon {to_roman(sermon_num)}',
                'subtitle': scripture,
                'author': 'cyril',
                'author_full': 'Cyril of Alexandria',
                'work': 'Commentary on Luke',
                'scripture_reference': scripture_ref,
                'themes': [],
                'date_delivered': None,
                'word_count': sum(len(p.split()) for p in paragraphs),
                'excerpt': paragraphs[0][:200] + '...' if paragraphs else '',
                'source_file': file_name,
                'extraction_method': 'html_parse',
                'has_footnotes': False,
                'footnotes': {},
                'verified': True
            }
            
            with open(sermon_dir / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            with open(sermon_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2, ensure_ascii=False)
            
            print(f"  Sermon {sermon_num}: {len(paragraphs)} paragraphs")

def main():
    print("Cyril Luke Simple Parser")
    print("=" * 60)
    process_all_files()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Parse Chrysostom Matthew homilies from ThML format and extract content with footnote markers.
Generates content.json files for each homily.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

def clean_text(text):
    """Clean text while preserving structure."""
    if not text:
        return ""
    # Handle HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&quot;', '"')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_homily_content(soup, homily_num):
    """Extract content for a specific homily from ThML."""
    roman = to_roman(homily_num)
    
    # Find homily start - try different patterns
    patterns = [
        f"Homily {roman}\\.",
        f"HOMILY {roman}\\.",
        f"Homily {homily_num}\\.",
        f"HOMILY {homily_num}\\."
    ]
    
    homily_start = None
    for pattern in patterns:
        # Find text containing the pattern
        for elem in soup.find_all(text=re.compile(pattern)):
            parent = elem.parent
            if parent:
                homily_start = parent
                break
        if homily_start:
            break
    
    if not homily_start:
        return None, {}
    
    content = {
        'title': f'Homily {roman}',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_mapping = {}
    
    # Find next homily to determine end
    next_homily_start = None
    next_roman = to_roman(homily_num + 1)
    next_patterns = [
        f"Homily {next_roman}\\.",
        f"HOMILY {next_roman}\\.",
        f"Homily {homily_num + 1}\\.",
        f"HOMILY {homily_num + 1}\\."
    ]
    
    for pattern in next_patterns:
        for elem in soup.find_all(text=re.compile(pattern)):
            parent = elem.parent
            if parent and parent != homily_start:
                next_homily_start = parent
                break
        if next_homily_start:
            break
    
    # Extract content between homilies
    current = homily_start
    collecting = True
    
    while current and collecting:
        if current == next_homily_start:
            break
        
        # Process paragraphs
        if current.name == 'p' and current.get('class'):
            # Skip navigation and non-content paragraphs
            classes = current.get('class', [])
            if any(c in ['c44', 'c12', 'c23'] for c in classes):  # Content classes
                para_text = ""
                
                # Process paragraph content
                for element in current.descendants:
                    if element.name == 'note':
                        # Extract footnote
                        fn_id = element.get('n', str(len(footnote_mapping) + 1))
                        if fn_id not in footnote_mapping:
                            new_num = str(len(footnote_mapping) + 1)
                            footnote_mapping[fn_id] = new_num
                        
                        # Get footnote text from endnote
                        endnote = element.find('p', class_='endnote')
                        if endnote:
                            fn_text = clean_text(endnote.get_text())
                            footnotes[footnote_mapping[fn_id]] = fn_text
                        
                        para_text += f'<sup>f{footnote_mapping[fn_id]}</sup>'
                    elif element.name is None:
                        # Text node
                        para_text += str(element)
                
                para_text = clean_text(para_text)
                if para_text and not para_text.startswith('Homily'):
                    content['paragraphs'].append(para_text)
        
        # Get next sibling
        if hasattr(current, 'next_sibling'):
            current = current.next_sibling
        else:
            break
    
    return content, footnotes

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

def process_thml_source():
    """Process the ThML source file and extract all homilies."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    content_dir = base_dir / 'content'
    
    if not source_file.exists():
        print(f"Source file not found: {source_file}")
        return
    
    # Parse ThML/HTML
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Process each homily
    homilies_processed = 0
    total_footnotes = 0
    
    for homily_num in range(1, 91):  # Matthew has 90 homilies
        # Extract homily content
        content_data, footnotes = extract_homily_content(soup, homily_num)
        
        if not content_data or not content_data['paragraphs']:
            print(f"Homily {homily_num:3d}: No content extracted")
            continue
        
        # Create directory for this homily
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        # Save content.json
        content_file = homily_dir / 'content.json'
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, indent=2, ensure_ascii=False)
        
        # Update footnotes in metadata.json if it exists
        metadata_file = homily_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['footnotes'] = footnotes
            metadata['has_footnotes'] = len(footnotes) > 0
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        homilies_processed += 1
        total_footnotes += len(footnotes)
        print(f"Homily {homily_num:3d}: {len(content_data['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
    
    print(f"\nTotal homilies processed: {homilies_processed}")
    print(f"Total footnotes extracted: {total_footnotes}")

def main():
    print("Parsing Chrysostom Matthew content from ThML...")
    print("-" * 50)
    process_thml_source()

if __name__ == "__main__":
    main()
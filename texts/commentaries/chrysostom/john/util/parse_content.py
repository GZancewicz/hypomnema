#!/usr/bin/env python3
"""
Parse Chrysostom John homilies and extract content with footnote markers.
Generates content.json files for each homily.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

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

def extract_text_with_footnotes(element, footnotes):
    """Extract text from element, replacing footnotes with markers."""
    text = ""
    
    # Add element's text
    if element.text:
        text += element.text
    
    # Process all children
    for child in element:
        if child.tag in ['note', 'footnote']:
            # Extract footnote content
            fn_id = child.get('n', child.get('id', str(len(footnotes) + 1)))
            fn_text = ''.join(child.itertext())
            footnotes[fn_id] = clean_text(fn_text)
            # Add footnote marker
            text += f'<sup>f{fn_id}</sup>'
        else:
            # Recursively process child element
            text += extract_text_with_footnotes(child, footnotes)
        
        # Add tail text after child
        if child.tail:
            text += child.tail
    
    return text

def parse_homily(homily_elem):
    """Parse a single homily element."""
    content = {
        'title': '',
        'subtitle': '',
        'paragraphs': []
    }
    footnotes = {}
    
    # Extract title
    title_elem = homily_elem.find('.//title')
    if title_elem is not None:
        content['title'] = clean_text(''.join(title_elem.itertext()))
    
    # Extract subtitle
    subtitle_elem = homily_elem.find('.//subtitle')
    if subtitle_elem is not None:
        content['subtitle'] = clean_text(''.join(subtitle_elem.itertext()))
    
    # Extract paragraphs
    for para in homily_elem.findall('.//p'):
        para_text = extract_text_with_footnotes(para, footnotes)
        para_text = clean_text(para_text)
        if para_text:
            content['paragraphs'].append(para_text)
    
    return content, footnotes

def process_xml_source():
    """Process the XML source file and extract all homilies."""
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
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
    total_footnotes = 0
    
    for homily_num in range(1, 89):  # John has 88 homilies
        # Try different XPath patterns
        homily = root.find(f".//homily[@number='{homily_num}']")
        if homily is None:
            homily = root.find(f".//div[@id='homily{homily_num}']")
        if homily is None:
            homily = root.find(f".//div[@class='homily'][{homily_num}]")
        
        if homily is None:
            print(f"Homily {homily_num} not found in source")
            continue
        
        # Parse homily content
        content, footnotes = parse_homily(homily)
        
        if not content['paragraphs']:
            print(f"Homily {homily_num}: No content extracted")
            continue
        
        # Create directory for this homily
        homily_dir = content_dir / f'{homily_num:03d}'
        homily_dir.mkdir(parents=True, exist_ok=True)
        
        # Save content.json
        content_file = homily_dir / 'content.json'
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
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
        print(f"Homily {homily_num:3d}: {len(content['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
    
    print(f"\nTotal homilies processed: {homilies_processed}")
    print(f"Total footnotes extracted: {total_footnotes}")

def main():
    print("Parsing Chrysostom John content...")
    print("-" * 50)
    process_xml_source()

if __name__ == "__main__":
    main()
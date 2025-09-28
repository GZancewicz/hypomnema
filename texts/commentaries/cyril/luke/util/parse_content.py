#!/usr/bin/env python3
"""
Parse Cyril Luke sermons and extract content with footnote markers.
Generates content.json files for each sermon.
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

def extract_sermon_content(soup, sermon_num):
    """Extract content for a specific sermon from HTML."""
    # Find sermon boundary
    sermon_start = soup.find('a', {'name': f'C{sermon_num}'})
    if not sermon_start:
        sermon_start = soup.find('a', {'name': f'c{sermon_num}'})
    
    if not sermon_start:
        return None, {}
    
    # Find next sermon marker to determine end
    next_sermon = None
    for i in range(sermon_num + 1, sermon_num + 20):
        next_sermon = soup.find('a', {'name': f'C{i}'})
        if not next_sermon:
            next_sermon = soup.find('a', {'name': f'c{i}'})
        if next_sermon:
            break
    
    content = {
        'title': f'Sermon {sermon_num}',
        'subtitle': '',
        'paragraphs': []
    }
    
    footnotes = {}
    footnote_mapping = {}  # Map original numbers to sermon-specific numbers
    
    # Extract content between sermon markers
    current = sermon_start
    title_found = False
    
    while current and current != next_sermon:
        if hasattr(current, 'name'):
            # Look for title
            if current.name in ['h3', 'h2', 'b'] and not title_found:
                text = current.text.strip()
                if f'SERMON' in text.upper():
                    content['title'] = clean_text(text)
                    title_found = True
            
            # Process paragraphs
            elif current.name == 'p':
                para_text = ""
                
                # Walk through paragraph content
                for element in current.descendants:
                    if element.name == 'a':
                        href = element.get('href', '')
                        # Check for footnote reference
                        if href.startswith('#'):
                            original_num = href.replace('#', '')
                            # Map to sermon-specific number
                            if original_num not in footnote_mapping:
                                new_num = str(len(footnote_mapping) + 1)
                                footnote_mapping[original_num] = new_num
                            fn_num = footnote_mapping[original_num]
                            para_text += f'<sup>f{fn_num}</sup>'
                        elif element.text:
                            para_text += element.text
                    elif element.name is None:
                        # Text node
                        para_text += str(element)
                
                para_text = clean_text(para_text)
                if para_text:
                    content['paragraphs'].append(para_text)
        
        current = current.next_sibling
    
    # Extract footnote content for mapped footnotes
    for original_num, mapped_num in footnote_mapping.items():
        fn_anchor = soup.find('a', {'name': original_num})
        if fn_anchor:
            fn_text = ""
            next_elem = fn_anchor.next_sibling
            
            # Collect footnote text
            while next_elem:
                if hasattr(next_elem, 'name'):
                    if next_elem.name == 'a' and next_elem.get('name'):
                        break
                    if next_elem.name == 'p':
                        # Check if new footnote paragraph
                        first_child = next_elem.find('a', {'name': True})
                        if first_child:
                            break
                    if hasattr(next_elem, 'text'):
                        fn_text += next_elem.text
                else:
                    fn_text += str(next_elem)
                
                next_elem = next_elem.next_sibling
            
            # Clean footnote text
            fn_text = re.sub(r'^' + re.escape(original_num) + r'\.?\s*', '', fn_text)
            fn_text = clean_text(fn_text)
            if fn_text:
                footnotes[mapped_num] = fn_text
    
    return content, footnotes

def get_sermon_to_file_mapping():
    """Map sermon numbers to source HTML files."""
    mapping = {}
    
    file_ranges = [
        ('cyril_on_luke_01_sermons_01_11.htm', range(1, 12)),
        ('cyril_on_luke_02_sermons_12_25.htm', range(12, 26)),
        ('cyril_on_luke_03_sermons_27_38.htm', range(27, 39)),
        ('cyril_on_luke_04_sermons_39_46.htm', range(39, 47)),
        ('cyril_on_luke_05_sermons_47_56.htm', range(47, 57)),
        ('cyril_on_luke_06_sermons_57_65.htm', range(57, 66)),
        ('cyril_on_luke_07_sermons_66_80.htm', range(66, 81)),
        ('cyril_on_luke_08_sermons_81_88.htm', range(81, 89)),
        ('cyril_on_luke_09_sermons_89_98.htm', range(89, 99)),
        ('cyril_on_luke_10_sermons_99_109.htm', range(99, 110)),
        ('cyril_on_luke_11_sermons_110_123.htm', range(110, 124)),
        ('cyril_on_luke_12_sermons_124_134.htm', range(124, 135)),
        ('cyril_on_luke_13_sermons_135_145.htm', range(135, 146)),
        ('cyril_on_luke_14_sermons_146_156.htm', range(146, 157))
    ]
    
    for filename, sermon_range in file_ranges:
        for sermon_num in sermon_range:
            mapping[sermon_num] = filename
    
    return mapping

def process_html_sources():
    """Process HTML source files and extract all sermons."""
    base_dir = Path(__file__).parent.parent
    source_dir = base_dir / 'source'
    content_dir = base_dir / 'content'
    
    sermon_to_file = get_sermon_to_file_mapping()
    
    sermons_processed = 0
    total_footnotes = 0
    
    # Process each HTML file
    processed_files = set()
    
    for sermon_num in range(1, 154):  # Cyril has 153 sermons
        # Skip missing sermons (26-38 are missing)
        if 26 <= sermon_num <= 38:
            print(f"Sermon {sermon_num:3d}: Skipped (missing in manuscript)")
            continue
        
        source_file = sermon_to_file.get(sermon_num)
        if not source_file:
            print(f"Sermon {sermon_num:3d}: No source file mapping")
            continue
        
        html_path = source_dir / source_file
        if not html_path.exists():
            print(f"Sermon {sermon_num:3d}: Source file not found")
            continue
        
        # Parse HTML file if not already parsed
        if source_file not in processed_files:
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            processed_files.add(source_file)
        
        # Extract sermon content
        content, footnotes = extract_sermon_content(soup, sermon_num)
        
        if not content or not content['paragraphs']:
            print(f"Sermon {sermon_num:3d}: No content extracted")
            continue
        
        # Create directory for this sermon
        sermon_dir = content_dir / f'{sermon_num:03d}'
        sermon_dir.mkdir(parents=True, exist_ok=True)
        
        # Save content.json
        content_file = sermon_dir / 'content.json'
        with open(content_file, 'w', encoding='utf-8') as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        
        # Update footnotes in metadata.json if it exists
        metadata_file = sermon_dir / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['footnotes'] = footnotes
            metadata['has_footnotes'] = len(footnotes) > 0
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        sermons_processed += 1
        total_footnotes += len(footnotes)
        print(f"Sermon {sermon_num:3d}: {len(content['paragraphs'])} paragraphs, {len(footnotes)} footnotes")
    
    print(f"\nTotal sermons processed: {sermons_processed}")
    print(f"Total footnotes extracted: {total_footnotes}")

def main():
    print("Parsing Cyril Luke content...")
    print("-" * 50)
    process_html_sources()

if __name__ == "__main__":
    main()
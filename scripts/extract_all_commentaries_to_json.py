#!/usr/bin/env python3
"""
Extract all commentaries (Chrysostom Matthew/John, Cyril Luke) to unified JSON format.
This creates a clean abstraction barrier between raw source files and displayed content.
"""

import json
import re
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any
from html.parser import HTMLParser

class HTMLTextExtractor(HTMLParser):
    """Extract text from HTML, converting certain tags to markdown-like format"""
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.in_italics = False
        self.in_bold = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ['i', 'em']:
            self.text_parts.append('<em>')
            self.in_italics = True
        elif tag in ['b', 'strong']:
            self.text_parts.append('<strong>')
            self.in_bold = True
        elif tag == 'br':
            self.text_parts.append('\n')
        elif tag == 'p':
            if self.text_parts and self.text_parts[-1] != '\n\n':
                self.text_parts.append('\n\n')
    
    def handle_endtag(self, tag):
        if tag in ['i', 'em']:
            self.text_parts.append('</em>')
            self.in_italics = False
        elif tag in ['b', 'strong']:
            self.text_parts.append('</strong>')
            self.in_bold = False
        elif tag == 'p':
            if self.text_parts and self.text_parts[-1] != '\n\n':
                self.text_parts.append('\n\n')
    
    def handle_data(self, data):
        self.text_parts.append(data)
    
    def get_text(self):
        return ''.join(self.text_parts)

def clean_text(text):
    """Clean and normalize text"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Normalize paragraph breaks
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def roman_to_int(s):
    """Convert Roman numeral to integer"""
    roman = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    total = 0
    prev_value = 0
    for char in reversed(s):
        value = roman.get(char, 0)
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    return total

def extract_text_from_element(elem):
    """Extract text from XML element, preserving some formatting"""
    text_parts = []
    
    def process_node(node):
        # Add text before any child elements
        if node.text:
            text_parts.append(node.text)
        
        # Process child elements
        for child in node:
            if child.tag == 'note':
                # Skip footnotes - they're handled separately
                continue
            elif child.tag == 'scripRef':
                # Include scripture references as plain text
                if child.text:
                    text_parts.append(child.text)
            elif child.tag == 'hi' and child.get('rend') == 'italic':
                text_parts.append('<em>')
                if child.text:
                    text_parts.append(child.text)
                text_parts.append('</em>')
            elif child.tag == 'hi' and child.get('rend') == 'bold':
                text_parts.append('<strong>')
                if child.text:
                    text_parts.append(child.text)
                text_parts.append('</strong>')
            else:
                # Recursively process other elements
                process_node(child)
            
            # Add text after the child element
            if child.tail:
                text_parts.append(child.tail)
    
    process_node(elem)
    return clean_text(''.join(text_parts))

def extract_chrysostom_homilies(book):
    """Extract Chrysostom homilies for Matthew or John"""
    base_dir = Path(f'../texts/commentaries/chrysostom/{book}')
    xml_file = base_dir / f'chrysostom_{book}_homilies.xml'
    
    if not xml_file.exists():
        print(f"Warning: {xml_file} not found")
        return {}
    
    # Load existing footnotes
    footnotes_file = base_dir / 'all_footnotes.json'
    with open(footnotes_file, 'r', encoding='utf-8') as f:
        all_footnotes = json.load(f)
    
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    homilies = {}
    
    # Find all homilies (ThML uses div2 with type="Homily")
    for div in root.findall('.//div2[@type="Homily"]'):
        homily_num_str = div.get('n')
        if not homily_num_str:
            continue
        
        # Convert Roman numerals to Arabic
        roman_to_arabic = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}
        # Simple conversion for common Roman numerals (extend as needed)
        if homily_num_str in roman_to_arabic:
            homily_num = str(roman_to_arabic[homily_num_str])
        else:
            # Try to parse complex Roman numerals
            try:
                homily_num = str(roman_to_int(homily_num_str))
            except:
                continue
        
        homily_data = {
            'number': int(homily_num),
            'author': 'John Chrysostom',
            'book': book.capitalize(),
            'type': 'homily',
            'title': f"Homily {homily_num}",
            'content': [],
            'footnotes': all_footnotes.get(homily_num, [])
        }
        
        # Extract content paragraphs
        # ThML uses div3 for paragraphs/sections
        for elem in div.findall('.//*'):
            if elem.tag in ['p', 'div3']:
                text = extract_text_from_element(elem)
                if text and len(text) > 20:  # Skip very short fragments
                    homily_data['content'].append({
                        'type': 'paragraph',
                        'text': text
                    })
        
        # Store verse reference if available
        verse_ref = None
        first_p = div.find('.//p')
        if first_p is not None and first_p.text:
            # Look for verse patterns
            verse_match = re.match(r'^((?:Matt\.|Matthew|John)\s+[IVXivx]+\.\s*\d+[^.]*\.)', first_p.text)
            if verse_match:
                verse_ref = verse_match.group(1).strip()
                homily_data['verse_reference'] = verse_ref
        
        homilies[homily_num] = homily_data
    
    return homilies

def extract_cyril_sermons():
    """Extract Cyril sermons on Luke from the multi-sermon HTML files"""
    base_dir = Path('../texts/commentaries/cyril/luke')
    
    # Load existing footnotes
    footnotes_file = base_dir / 'footnotes.json'
    with open(footnotes_file, 'r', encoding='utf-8') as f:
        all_footnotes = json.load(f)
    
    sermons = {}
    
    # Process all sermon HTML files
    html_files = [
        'cyril_on_luke_01_sermons_01_11.htm',
        'cyril_on_luke_02_sermons_12_25.htm',
        'cyril_on_luke_03_sermons_27_38.htm',
        'cyril_on_luke_04_sermons_39_46.htm',
        'cyril_on_luke_05_sermons_47_56.htm',
        'cyril_on_luke_06_sermons_57_65.htm',
        'cyril_on_luke_07_sermons_66_80.htm',
        'cyril_on_luke_08_sermons_81_88.htm',
        'cyril_on_luke_09_sermons_89_98.htm',
        'cyril_on_luke_10_sermons_99_109.htm',
        'cyril_on_luke_11_sermons_110_123.htm',
        'cyril_on_luke_12_sermons_124_134.htm',
        'cyril_on_luke_13_sermons_135_145.htm',
        'cyril_on_luke_14_sermons_146_156.htm'
    ]
    
    for html_filename in html_files:
        html_file = base_dir / html_filename
        if not html_file.exists():
            continue
            
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Extract individual sermons from the file
        # Pattern to find sermon headers like "SERMON I." or "SERMON CXLVI."
        sermon_pattern = r'<h3[^>]*><strong>.*?SERMON\s+([IVXLCDM]+)\..*?</strong></h3>'
        sermon_matches = list(re.finditer(sermon_pattern, html_content, re.IGNORECASE))
        
        for i, match in enumerate(sermon_matches):
            roman_num = match.group(1)
            sermon_num = str(roman_to_int(roman_num))
            
            # Get sermon content (from this header to next header or end)
            start_pos = match.end()
            if i < len(sermon_matches) - 1:
                end_pos = sermon_matches[i + 1].start()
            else:
                # Last sermon in file - go to end or footnotes section
                end_match = re.search(r'<h3[^>]*>.*?Notes.*?</h3>', html_content[start_pos:], re.IGNORECASE)
                if end_match:
                    end_pos = start_pos + end_match.start()
                else:
                    end_pos = len(html_content)
            
            sermon_content = html_content[start_pos:end_pos]
        
            sermon_data = {
                'number': int(sermon_num),
                'author': 'Cyril of Alexandria',
                'book': 'Luke',
                'type': 'sermon',
                'title': f"Sermon {roman_num}",
                'roman_numeral': roman_num,
                'content': [],
                'footnotes': all_footnotes.get(sermon_num, [])
            }
            
            # Extract verse reference from the beginning
            verse_match = re.search(r'<blockquote>\s*<p>(Luke\s+[ivxIVX]+\.\s*\d+[^<]*)</p>\s*</blockquote>', sermon_content, re.IGNORECASE)
            if verse_match:
                sermon_data['verse_reference'] = verse_match.group(1).strip()
            
            # Parse the HTML content
            parser = HTMLTextExtractor()
            parser.feed(sermon_content)
            text = parser.get_text()
            
            # Clean up and split into paragraphs
            text = re.sub(r'\n\s*\n+', '\n\n', text)
            paragraphs = text.split('\n\n')
            
            for para in paragraphs:
                para = para.strip()
                # Skip headers, verse references, and short fragments
                if para and len(para) > 30 and not re.match(r'^(Luke|SERMON|Notes)', para, re.IGNORECASE):
                    sermon_data['content'].append({
                        'type': 'paragraph',
                        'text': para
                    })
            
            sermons[sermon_num] = sermon_data
    
    return sermons

def create_unified_json():
    """Create unified JSON files for all commentaries"""
    output_dir = Path('../texts/commentaries/unified_json')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Process Chrysostom Matthew
    print("Extracting Chrysostom Matthew homilies...")
    matthew_homilies = extract_chrysostom_homilies('matthew')
    with open(output_dir / 'chrysostom_matthew.json', 'w', encoding='utf-8') as f:
        json.dump(matthew_homilies, f, indent=2, ensure_ascii=False)
    print(f"  Extracted {len(matthew_homilies)} Matthew homilies")
    
    # Process Chrysostom John
    print("Extracting Chrysostom John homilies...")
    john_homilies = extract_chrysostom_homilies('john')
    with open(output_dir / 'chrysostom_john.json', 'w', encoding='utf-8') as f:
        json.dump(john_homilies, f, indent=2, ensure_ascii=False)
    print(f"  Extracted {len(john_homilies)} John homilies")
    
    # Process Cyril Luke
    print("Extracting Cyril Luke sermons...")
    luke_sermons = extract_cyril_sermons()
    with open(output_dir / 'cyril_luke.json', 'w', encoding='utf-8') as f:
        json.dump(luke_sermons, f, indent=2, ensure_ascii=False)
    print(f"  Extracted {len(luke_sermons)} Luke sermons")
    
    # Create a manifest file
    manifest = {
        'format_version': '1.0',
        'description': 'Unified commentary format for Hypomnema',
        'structure': {
            'number': 'Commentary number (integer)',
            'author': 'Author name',
            'book': 'Biblical book',
            'type': 'homily or sermon',
            'title': 'Display title',
            'verse_reference': 'Optional verse reference',
            'content': [
                {
                    'type': 'paragraph',
                    'text': 'Paragraph text with <em> and <strong> tags'
                }
            ],
            'footnotes': [
                {
                    'number': 'Footnote number',
                    'content': 'Footnote text'
                }
            ]
        },
        'files': [
            'chrysostom_matthew.json',
            'chrysostom_john.json',
            'cyril_luke.json'
        ]
    }
    
    with open(output_dir / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    print("\nUnified JSON extraction complete!")
    print(f"Files created in: {output_dir}")

if __name__ == '__main__':
    create_unified_json()
#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import json
import re
from html import unescape

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    
    # Unescape HTML entities
    text = unescape(text)
    
    return text.strip()

def extract_text_from_element(elem):
    """Extract all text from an element, converting scripRef to just the reference text"""
    text_parts = []
    
    # Get the text before any child elements
    if elem.text:
        text_parts.append(elem.text)
    
    # Process child elements
    for child in elem:
        # For scripRef tags, extract just the text content (the reference)
        if child.tag == 'scripRef':
            if child.text:
                text_parts.append(child.text.strip())
            # Also get text from nested elements in scripRef
            for subchild in child:
                if subchild.text:
                    text_parts.append(subchild.text.strip())
                if subchild.tail:
                    text_parts.append(subchild.tail.strip())
        else:
            # For other tags, get their text content recursively
            child_text = extract_text_from_element(child)
            if child_text:
                text_parts.append(child_text)
        
        # Get any text after the child element
        if child.tail:
            text_parts.append(child.tail)
    
    # Join all parts and clean
    return clean_text(' '.join(text_parts))

def extract_homily_number(div_elem):
    """Extract homily number from div element"""
    # First check the 'n' attribute which directly has the Roman numeral
    n_attr = div_elem.get('n', '')
    if n_attr:
        arabic = roman_to_arabic(n_attr)
        if arabic:
            return arabic
    
    # Check the id attribute for patterns
    div_id = div_elem.get('id', '')
    
    # Look for HOMILY text in the content
    for elem in div_elem.iter():
        if elem.text and 'HOMILY' in elem.text.upper():
            match = re.search(r'HOMILY\s+([IVXLC]+)', elem.text.upper())
            if match:
                return roman_to_arabic(match.group(1))
    
    return None

def roman_to_arabic(roman):
    """Convert Roman numeral to Arabic number"""
    if not roman:
        return None
        
    roman = roman.upper()
    values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50, 
        'C': 100, 'D': 500, 'M': 1000
    }
    
    total = 0
    prev_value = 0
    
    for char in reversed(roman):
        if char not in values:
            return None
        value = values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    
    return total

def extract_all_footnotes(xml_file):
    """Extract all footnotes from the XML file organized by homily"""
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    homilies_footnotes = {}
    processed_notes = set()  # Track processed note IDs to avoid duplicates
    
    # Process all div2 elements that contain homilies
    for div in root.iter('div2'):
        # Check if this is a homily div
        div_type = div.get('type', '')
        
        if 'homily' in div_type.lower():
            # Try to extract homily number
            homily_num = extract_homily_number(div)
            if homily_num:
                print(f"Processing Homily {homily_num}")
                if homily_num not in homilies_footnotes:
                    homilies_footnotes[homily_num] = []
                
                # Find all note elements within this homily div
                for note in div.iter('note'):
                    note_id = note.get('id', '')
                    note_n = note.get('n', '')
                    
                    # Skip if we've already processed this note
                    if note_id and note_id in processed_notes:
                        continue
                    
                    if note_n:  # Only process notes with a number
                        # Extract content from the note
                        content = extract_text_from_element(note)
                        
                        if content:
                            footnote = {
                                'homily': homily_num,
                                'original_number': note_n,
                                'content': content,
                                'id': note_id
                            }
                            homilies_footnotes[homily_num].append(footnote)
                            
                            if note_id:
                                processed_notes.add(note_id)
    
    # Renumber footnotes sequentially within each homily
    for homily_num in homilies_footnotes:
        footnotes = homilies_footnotes[homily_num]
        # Sort by original number (handle both numeric and alphanumeric)
        footnotes.sort(key=lambda x: (int(re.sub(r'\D', '', x['original_number']) or 0), x['original_number']))
        
        # Assign sequential display numbers
        for i, footnote in enumerate(footnotes, 1):
            footnote['display_number'] = i
    
    return homilies_footnotes

def main():
    xml_file = '../texts/commentaries/chrysostom/john/chrysostom_john_homilies.xml'
    output_file = '../texts/commentaries/chrysostom/john/all_footnotes.json'
    
    print(f"Extracting footnotes from {xml_file}")
    
    try:
        homilies_footnotes = extract_all_footnotes(xml_file)
        
        # Convert to a more accessible format
        output_data = {}
        total_footnotes = 0
        
        for homily_num in sorted(homilies_footnotes.keys()):
            footnotes = homilies_footnotes[homily_num]
            output_data[str(homily_num)] = footnotes
            total_footnotes += len(footnotes)
            print(f"  Homily {homily_num}: {len(footnotes)} footnotes")
        
        # Save to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nTotal footnotes extracted: {total_footnotes}")
        print(f"Output saved to: {output_file}")
        
    except Exception as e:
        print(f"Error processing XML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
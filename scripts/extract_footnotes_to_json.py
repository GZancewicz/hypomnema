#!/usr/bin/env python3
"""
Extract footnotes from Chrysostom's Matthew homilies ThML file to JSON.
"""

import re
import json
from collections import defaultdict
import html

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    for char in reversed(roman):
        value = values.get(char, 0)
        if value < prev:
            total -= value
        else:
            total += value
        prev = value
    return total

def extract_footnotes_from_xml(xml_path):
    """Extract all footnotes from the ThML file."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    footnotes_by_homily = defaultdict(list)
    
    # Find all homily div2 sections
    homily_pattern = r'<div2[^>]*n="([IVX]+)"[^>]*>(.*?)</div2>'
    homily_matches = re.finditer(homily_pattern, content, re.DOTALL)
    
    for homily_match in homily_matches:
        homily_roman = homily_match.group(1)
        homily_num = roman_to_int(homily_roman)
        homily_content = homily_match.group(2)
        
        # Find all notes within this homily
        note_pattern = r'<note\s+n="(\d+)"[^>]*>(.*?)</note>'
        note_matches = re.finditer(note_pattern, homily_content, re.DOTALL)
        
        homily_footnotes = []
        for i, note_match in enumerate(note_matches, 1):
            original_num = note_match.group(1)
            note_content = note_match.group(2)
            
            # Extract text content from the note
            # Remove the <p class="endnote"> wrapper
            text_pattern = r'<p[^>]*>(.*?)</p>'
            text_match = re.search(text_pattern, note_content, re.DOTALL)
            
            if text_match:
                text = text_match.group(1)
            else:
                text = note_content
            
            # Clean up the text
            # Remove HTML tags but preserve Greek text
            text = re.sub(r'<span[^>]*lang="EL"[^>]*>([^<]+)</span>', r'[Greek: \1]', text)
            text = re.sub(r'<[^>]+>', '', text)
            text = html.unescape(text)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Remove square brackets at beginning and end if present
            if text.startswith('[') and text.endswith(']'):
                text = text[1:-1]
            
            footnote = {
                "original_number": int(original_num),
                "display_number": i,  # Sequential number within homily
                "content": text
            }
            
            homily_footnotes.append(footnote)
        
        if homily_footnotes:
            footnotes_by_homily[homily_num] = {
                "roman_numeral": homily_roman,
                "footnotes": homily_footnotes
            }
    
    # Also check for Homily I if it's in a different format
    # Sometimes Homily I doesn't have a div2 wrapper
    if 1 not in footnotes_by_homily:
        # Look for content after "Homily I." and before "Homily II."
        homily1_pattern = r'Homily I\.</span></p>(.*?)(?=Homily II\.|<div2[^>]*n="II")'
        homily1_match = re.search(homily1_pattern, content, re.DOTALL)
        
        if homily1_match:
            homily1_content = homily1_match.group(1)
            note_pattern = r'<note\s+n="(\d+)"[^>]*>(.*?)</note>'
            note_matches = re.finditer(note_pattern, homily1_content, re.DOTALL)
            
            homily1_footnotes = []
            for i, note_match in enumerate(note_matches, 1):
                original_num = note_match.group(1)
                note_content = note_match.group(2)
                
                # Extract text content
                text_pattern = r'<p[^>]*>(.*?)</p>'
                text_match = re.search(text_pattern, note_content, re.DOTALL)
                
                if text_match:
                    text = text_match.group(1)
                else:
                    text = note_content
                
                # Clean up
                text = re.sub(r'<span[^>]*lang="EL"[^>]*>([^<]+)</span>', r'[Greek: \1]', text)
                text = re.sub(r'<[^>]+>', '', text)
                text = html.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if text.startswith('[') and text.endswith(']'):
                    text = text[1:-1]
                
                footnote = {
                    "original_number": int(original_num),
                    "display_number": i,
                    "content": text
                }
                
                homily1_footnotes.append(footnote)
            
            if homily1_footnotes:
                footnotes_by_homily[1] = {
                    "roman_numeral": "I",
                    "footnotes": homily1_footnotes
                }
    
    return dict(footnotes_by_homily)

def main():
    xml_path = "texts/commentaries/chrysostom/matthew/chrysostom_matthew_homilies.xml"
    output_path = "texts/commentaries/chrysostom/matthew/footnotes.json"
    
    print("Extracting footnotes from ThML file...")
    footnotes = extract_footnotes_from_xml(xml_path)
    
    # Sort by homily number
    sorted_footnotes = dict(sorted(footnotes.items()))
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_footnotes, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\nExtracted footnotes from {len(sorted_footnotes)} homilies:")
    for homily_num, data in sorted_footnotes.items():
        print(f"  Homily {data['roman_numeral']}: {len(data['footnotes'])} footnotes")
    
    print(f"\nSaved to {output_path}")

if __name__ == "__main__":
    main()
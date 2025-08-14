#!/usr/bin/env python3
"""
Analyze ThML structure to understand homily organization.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_structure():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all homily references with context
    pattern = r'(Homily [IVX]+\.)'
    matches = re.finditer(pattern, content)
    
    homilies = {}
    for match in matches:
        homily_text = match.group(1)
        position = match.start()
        
        # Get context
        start = max(0, position - 100)
        end = min(len(content), position + 200)
        context = content[start:end]
        
        # Extract roman numeral
        roman_match = re.search(r'Homily ([IVX]+)\.', homily_text)
        if roman_match:
            roman = roman_match.group(1)
            if roman not in homilies:
                homilies[roman] = []
            homilies[roman].append({
                'position': position,
                'context': context.replace('\n', ' ').strip()
            })
    
    print(f"Found {len(homilies)} unique homily numbers")
    print("\nHomily distribution:")
    
    # Convert and sort
    def roman_to_int(s):
        values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
        total = 0
        prev = 0
        for char in reversed(s):
            val = values.get(char, 0)
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
        return total
    
    sorted_homilies = sorted(homilies.items(), key=lambda x: roman_to_int(x[0]))
    
    for roman, occurrences in sorted_homilies:
        print(f"  Homily {roman}: {len(occurrences)} occurrence(s) at position(s): {[o['position'] for o in occurrences]}")
    
    # Check for pattern in positions
    print("\nAnalyzing document structure...")
    
    # Parse with BeautifulSoup using XML parser
    soup = BeautifulSoup(content, 'xml')
    
    # Find all div3 elements (likely homily containers)
    div3s = soup.find_all('div3')
    print(f"Found {len(div3s)} div3 elements")
    
    # Find all div2 elements
    div2s = soup.find_all('div2')
    print(f"Found {len(div2s)} div2 elements")
    
    # Look for specific patterns
    for i, div3 in enumerate(div3s[:5]):  # Check first 5
        id_attr = div3.get('id', '')
        print(f"  div3[{i}] id: {id_attr}")
        
        # Check for homily content
        text = div3.get_text()[:200]
        if 'Homily' in text:
            match = re.search(r'Homily [IVX]+\.', text)
            if match:
                print(f"    Contains: {match.group()}")

if __name__ == "__main__":
    analyze_structure()
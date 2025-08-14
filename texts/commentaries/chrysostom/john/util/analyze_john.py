#!/usr/bin/env python3
"""
Analyze John ThML structure to understand homily organization.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def roman_to_int(roman):
    """Convert Roman numeral to integer."""
    if not roman:
        return None
    values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    total = 0
    prev = 0
    for char in reversed(roman):
        if char in values:
            val = values[char]
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
    return total if total > 0 else None

def analyze_structure():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Find all div2 elements with type='Homily'
    div2s = soup.find_all('div2', type='Homily')
    print(f"Found {len(div2s)} div2 elements with type='Homily'\n")
    
    homily_numbers = []
    homily_map = {}
    
    for i, div2 in enumerate(div2s):
        n_attr = div2.get('n', '')
        id_attr = div2.get('id', '')
        
        # Convert n attribute to number
        num = roman_to_int(n_attr)
        if num:
            homily_numbers.append(num)
            if num not in homily_map:
                homily_map[num] = []
            homily_map[num].append({'n': n_attr, 'id': id_attr})
    
    print(f"Unique homily numbers: {sorted(set(homily_numbers))}")
    print(f"\nTotal unique homilies: {len(set(homily_numbers))}")
    
    # Check for duplicates
    print("\nHomilies with multiple div2 elements:")
    for num in sorted(homily_map.keys()):
        if len(homily_map[num]) > 1:
            print(f"  Homily {num} ({homily_map[num][0]['n']}): {len(homily_map[num])} div2 elements")
            for elem in homily_map[num]:
                print(f"    id: {elem['id']}")
    
    # Check for missing numbers
    missing = []
    for i in range(1, 89):
        if i not in homily_numbers:
            missing.append(i)
    
    if missing:
        print(f"\nMissing homily numbers: {missing}")
    else:
        print("\nAll 88 homilies found!")

if __name__ == "__main__":
    analyze_structure()
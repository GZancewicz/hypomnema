#!/usr/bin/env python3
"""
Analyze all div2 elements to find homilies.
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

def analyze_all_div2():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Find all div2 elements with type="Homily"
    div2s = soup.find_all('div2', type='Homily')
    print(f"Found {len(div2s)} div2 elements with type='Homily'\n")
    
    homily_numbers = []
    
    for i, div2 in enumerate(div2s):
        n_attr = div2.get('n', '')
        
        # Convert n attribute to number
        num = roman_to_int(n_attr)
        if num:
            homily_numbers.append(num)
            
            # Get scripture reference
            text = div2.get_text()[:500]
            scripture = ""
            match = re.search(r'Matt?(?:hew)?\.?\s*(\d+)[:\.](\d+(?:-\d+)?)', text)
            if match:
                scripture = f"Matthew {match.group(1)}:{match.group(2)}"
            
            print(f"Homily {num:3d} (n='{n_attr}'): {scripture}")
    
    print(f"\nTotal homilies found: {len(homily_numbers)}")
    print(f"Range: {min(homily_numbers)} - {max(homily_numbers)}")
    
    # Check for missing numbers
    missing = []
    for i in range(1, 91):
        if i not in homily_numbers:
            missing.append(i)
    
    if missing:
        print(f"\nMissing homily numbers: {missing}")
    else:
        print("\nAll 90 homilies found!")

if __name__ == "__main__":
    analyze_all_div2()
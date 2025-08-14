#!/usr/bin/env python3
"""
Check all div2 elements in John ThML.
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

def check_all_div2():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Find ALL div2 elements
    all_div2s = soup.find_all('div2')
    print(f"Total div2 elements: {len(all_div2s)}\n")
    
    # Group by type
    by_type = {}
    for div2 in all_div2s:
        type_attr = div2.get('type', 'no_type')
        if type_attr not in by_type:
            by_type[type_attr] = []
        by_type[type_attr].append(div2)
    
    print("div2 elements by type:")
    for type_name, elements in by_type.items():
        print(f"  {type_name}: {len(elements)} elements")
        
        # If not Homily, check what n values they have
        if type_name != 'Homily':
            n_values = []
            for elem in elements[:5]:  # Check first 5
                n_attr = elem.get('n', '')
                if n_attr:
                    n_values.append(n_attr)
            if n_values:
                print(f"    Sample n values: {n_values}")
    
    # Check for homily text in non-Homily div2s
    print("\nChecking for homily content in non-Homily div2s:")
    for type_name, elements in by_type.items():
        if type_name != 'Homily':
            for elem in elements:
                text = elem.get_text()[:500]
                if re.search(r'Homily [IVX]+\.', text):
                    match = re.search(r'Homily ([IVX]+)\.', text)
                    if match:
                        print(f"  Found '{match.group()}' in div2 with type='{type_name}', n='{elem.get('n', '')}', id='{elem.get('id', '')}'")

if __name__ == "__main__":
    check_all_div2()
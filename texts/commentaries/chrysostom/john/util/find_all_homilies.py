#!/usr/bin/env python3
"""
Find all homilies in John ThML including those in p elements.
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

def find_all_homilies():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_john_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Find homilies in div2 elements
    div2s = soup.find_all('div2', type='Homily')
    div2_homilies = set()
    for div2 in div2s:
        n_attr = div2.get('n', '')
        num = roman_to_int(n_attr)
        if num:
            div2_homilies.add(num)
    
    print(f"Homilies in div2 elements: {sorted(div2_homilies)}")
    print(f"Total: {len(div2_homilies)}\n")
    
    # Find homilies in p/span elements
    p_homilies = {}
    pattern = re.compile(r'Homily\s+([IVX]+)\.')
    
    for p in soup.find_all('p'):
        span = p.find('span')
        if span:
            text = span.get_text()
            match = pattern.match(text)
            if match:
                roman = match.group(1)
                num = roman_to_int(roman)
                if num and num not in div2_homilies:  # Only if not already in div2
                    p_id = p.get('id', '')
                    p_homilies[num] = {'roman': roman, 'id': p_id}
    
    print(f"Additional homilies in p/span elements: {sorted(p_homilies.keys())}")
    print(f"Total: {len(p_homilies)}")
    
    # Combined total
    all_homilies = div2_homilies.union(set(p_homilies.keys()))
    print(f"\nAll homilies found: {sorted(all_homilies)}")
    print(f"Total: {len(all_homilies)}")
    
    # Check for missing
    missing = []
    for i in range(1, 89):
        if i not in all_homilies:
            missing.append(i)
    
    if missing:
        print(f"\nMissing homily numbers: {missing}")
    
    # Show some p/span homily IDs for reference
    if p_homilies:
        print(f"\nSample p/span homily IDs:")
        for num in sorted(list(p_homilies.keys())[:10]):
            print(f"  Homily {num}: id='{p_homilies[num]['id']}'")

if __name__ == "__main__":
    find_all_homilies()
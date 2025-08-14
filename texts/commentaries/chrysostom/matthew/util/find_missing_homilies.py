#!/usr/bin/env python3
"""
Find missing homilies 87-90.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def find_missing_homilies():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Search for the missing homilies by text
    missing_romans = ['LXXXVII', 'LXXXVIII', 'LXXXIX', 'XC']
    
    for roman in missing_romans:
        print(f"\nSearching for Homily {roman}:")
        
        # Search in all elements
        pattern = re.compile(f'Homily\\s+{roman}[^I]')
        
        # Find in text
        elements = soup.find_all(string=pattern)
        for elem in elements:
            parent = elem.parent
            print(f"  Found in {parent.name} tag")
            print(f"    id: {parent.get('id', 'no id')}")
            print(f"    class: {parent.get('class', 'no class')}")
            print(f"    Text: {elem[:100]}")
            
            # Check parent's parent
            if parent.parent:
                pp = parent.parent
                print(f"    Parent: {pp.name} (id={pp.get('id', 'no id')})")

if __name__ == "__main__":
    find_missing_homilies()
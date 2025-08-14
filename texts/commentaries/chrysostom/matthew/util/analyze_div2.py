#!/usr/bin/env python3
"""
Analyze div2 structure to understand homily organization.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

def analyze_div2_structure():
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / 'source' / 'chrysostom_matthew_homilies.xml'
    
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'xml')
    
    # Find all div2 elements
    div2s = soup.find_all('div2')
    print(f"Found {len(div2s)} div2 elements\n")
    
    homily_count = 0
    for i, div2 in enumerate(div2s):
        id_attr = div2.get('id', '')
        n_attr = div2.get('n', '')
        type_attr = div2.get('type', '')
        
        # Get first 200 chars of text
        text = div2.get_text()[:200].replace('\n', ' ').strip()
        
        # Check if it contains "Homily"
        if 'Homily' in text or 'HOMILY' in text:
            homily_count += 1
            print(f"div2[{i}]:")
            print(f"  id: {id_attr}")
            print(f"  n: {n_attr}")
            print(f"  type: {type_attr}")
            
            # Extract homily number from text
            match = re.search(r'Homily\s+([IVX]+)\.', text)
            if match:
                print(f"  Homily: {match.group(1)}")
            
            # Check for scripture reference
            match = re.search(r'Matt?(?:hew)?\.?\s*(\d+)[:\.](\d+(?:-\d+)?)', text)
            if match:
                print(f"  Scripture: Matthew {match.group(1)}:{match.group(2)}")
            
            print(f"  Text preview: {text[:100]}...")
            print()
    
    print(f"\nTotal div2s with Homily content: {homily_count}")

if __name__ == "__main__":
    analyze_div2_structure()
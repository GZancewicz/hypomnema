#!/usr/bin/env python3
import json
import os
import re
from pathlib import Path

def fix_duplicate_subtitle(content_dir):
    """Remove the first paragraph if it duplicates the subtitle"""
    
    fixed_count = 0
    
    # Iterate through all numbered directories
    for homily_dir in sorted(content_dir.iterdir()):
        if not homily_dir.is_dir():
            continue
            
        content_file = homily_dir / "content.json"
        if not content_file.exists():
            continue
            
        with open(content_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data.get('paragraphs'):
            continue
            
        first_para = data['paragraphs'][0]
        
        # Check if first paragraph is a duplicate subtitle (Matt. X. Y., John X. Y, or Homily XX)
        if re.match(r'^(Matt\.|John|JOHN|Homily [IVXLC]+)', first_para, re.IGNORECASE):
            print(f"Fixing {homily_dir.name}: removing '{first_para[:30]}...'")
            data['paragraphs'] = data['paragraphs'][1:]
            fixed_count += 1
            
            # Write back the fixed content
            with open(content_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    
    return fixed_count

if __name__ == "__main__":
    # Fix Matthew homilies
    matthew_dir = Path(__file__).parent.parent / "content"
    if matthew_dir.exists():
        print("Fixing Chrysostom Matthew homilies...")
        count = fix_duplicate_subtitle(matthew_dir)
        print(f"Fixed {count} homilies in Matthew")
    
    # Fix John homilies
    john_dir = Path(__file__).parent.parent.parent / "john" / "content"
    if john_dir.exists():
        print("\nFixing Chrysostom John homilies...")
        count = fix_duplicate_subtitle(john_dir)
        print(f"Fixed {count} homilies in John")
    
    # Fix Cyril Luke sermons
    cyril_dir = Path(__file__).parent.parent.parent.parent / "cyril" / "luke" / "content"
    if cyril_dir.exists():
        print("\nFixing Cyril Luke sermons...")
        count = fix_duplicate_subtitle(cyril_dir)
        print(f"Fixed {count} sermons in Luke")
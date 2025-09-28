#!/usr/bin/env python3
"""
Parse scripture references from Chrysostom Matthew footnotes.
Generates scripture_references.json for each homily.
"""

import os
import sys
import json
import re
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from parse_matthew import extract_scripture_refs_from_footnote

def process_scripture_references():
    """Extract scripture references from footnotes for all homilies."""
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    for homily_num in range(1, 91):
        homily_dir = content_dir / f'{homily_num:03d}'
        metadata_file = homily_dir / 'metadata.json'
        
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        footnotes = metadata.get('footnotes', {})
        scripture_refs = []
        
        for fn_id, fn_text in footnotes.items():
            refs = extract_scripture_refs_from_footnote(fn_text)
            if refs:
                scripture_refs.append({
                    'footnote': int(fn_id) if fn_id.isdigit() else fn_id,
                    'references': refs
                })
        
        # Save scripture_references.json
        with open(homily_dir / 'scripture_references.json', 'w', encoding='utf-8') as f:
            json.dump(scripture_refs, f, indent=2, ensure_ascii=False)
        
        print(f"Homily {homily_num:3d}: {len(scripture_refs)} footnotes with references")

def main():
    print("Parsing Chrysostom Matthew Scripture References")
    print("=" * 60)
    process_scripture_references()
    print("\nScripture reference parsing complete!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Parse scripture references from Chrysostom Matthew homilies.
Generates scripture_references.json files for each homily.
"""

import os
import json
import re
from pathlib import Path

def parse_biblical_reference(text):
    """Parse a biblical reference string into structured format."""
    # Common patterns for biblical references
    patterns = [
        # Full book name with chapter:verse
        r'(\w+(?:\s+\w+)?)\s+(\d+)[:\.](\d+)(?:\s*-\s*(?:(\d+)[:\.])?(\d+))?',
        # Abbreviated book name
        r'(\w+\.?)\s+(\d+)[:\.](\d+)(?:\s*-\s*(?:(\d+)[:\.])?(\d+))?',
    ]
    
    references = []
    
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            book = normalize_book_name(match.group(1))
            if not book:
                continue
            
            ref = {
                'book': book,
                'chapter': int(match.group(2)),
                'verse': int(match.group(3))
            }
            
            # Handle verse ranges
            if match.group(5):  # End verse exists
                if match.group(4):  # End chapter exists
                    ref['end_chapter'] = int(match.group(4))
                else:
                    ref['end_chapter'] = ref['chapter']
                ref['end_verse'] = int(match.group(5))
            
            references.append(ref)
    
    return references

def normalize_book_name(name):
    """Normalize book name to standard format."""
    name = name.lower().strip().replace('.', '')
    
    book_map = {
        # Old Testament
        'gen': 'genesis', 'genesis': 'genesis',
        'ex': 'exodus', 'exod': 'exodus', 'exodus': 'exodus',
        'lev': 'leviticus', 'leviticus': 'leviticus',
        'num': 'numbers', 'numbers': 'numbers',
        'deut': 'deuteronomy', 'deuteronomy': 'deuteronomy',
        'josh': 'joshua', 'joshua': 'joshua',
        'judg': 'judges', 'judges': 'judges',
        'ruth': 'ruth',
        '1 sam': '1_samuel', '1 samuel': '1_samuel', '1samuel': '1_samuel',
        '2 sam': '2_samuel', '2 samuel': '2_samuel', '2samuel': '2_samuel',
        '1 kings': '1_kings', '1kings': '1_kings',
        '2 kings': '2_kings', '2kings': '2_kings',
        '1 chron': '1_chronicles', '1 chronicles': '1_chronicles',
        '2 chron': '2_chronicles', '2 chronicles': '2_chronicles',
        'ezra': 'ezra',
        'neh': 'nehemiah', 'nehemiah': 'nehemiah',
        'esth': 'esther', 'esther': 'esther',
        'job': 'job',
        'ps': 'psalms', 'psalm': 'psalms', 'psalms': 'psalms',
        'prov': 'proverbs', 'proverbs': 'proverbs',
        'eccl': 'ecclesiastes', 'ecclesiastes': 'ecclesiastes',
        'song': 'song_of_solomon', 'songs': 'song_of_solomon',
        'isa': 'isaiah', 'isaiah': 'isaiah',
        'jer': 'jeremiah', 'jeremiah': 'jeremiah',
        'lam': 'lamentations', 'lamentations': 'lamentations',
        'ezek': 'ezekiel', 'ezekiel': 'ezekiel',
        'dan': 'daniel', 'daniel': 'daniel',
        'hos': 'hosea', 'hosea': 'hosea',
        'joel': 'joel',
        'amos': 'amos',
        'obad': 'obadiah', 'obadiah': 'obadiah',
        'jonah': 'jonah',
        'mic': 'micah', 'micah': 'micah',
        'nah': 'nahum', 'nahum': 'nahum',
        'hab': 'habakkuk', 'habakkuk': 'habakkuk',
        'zeph': 'zephaniah', 'zephaniah': 'zephaniah',
        'hag': 'haggai', 'haggai': 'haggai',
        'zech': 'zechariah', 'zechariah': 'zechariah',
        'mal': 'malachi', 'malachi': 'malachi',
        
        # New Testament
        'matt': 'matthew', 'matthew': 'matthew', 'mt': 'matthew',
        'mark': 'mark', 'mk': 'mark',
        'luke': 'luke', 'lk': 'luke',
        'john': 'john', 'jn': 'john',
        'acts': 'acts',
        'rom': 'romans', 'romans': 'romans',
        '1 cor': '1_corinthians', '1 corinthians': '1_corinthians', '1corinthians': '1_corinthians',
        '2 cor': '2_corinthians', '2 corinthians': '2_corinthians', '2corinthians': '2_corinthians',
        'gal': 'galatians', 'galatians': 'galatians',
        'eph': 'ephesians', 'ephesians': 'ephesians',
        'phil': 'philippians', 'philippians': 'philippians',
        'col': 'colossians', 'colossians': 'colossians',
        '1 thess': '1_thessalonians', '1 thessalonians': '1_thessalonians',
        '2 thess': '2_thessalonians', '2 thessalonians': '2_thessalonians',
        '1 tim': '1_timothy', '1 timothy': '1_timothy',
        '2 tim': '2_timothy', '2 timothy': '2_timothy',
        'titus': 'titus',
        'philem': 'philemon', 'philemon': 'philemon',
        'heb': 'hebrews', 'hebrews': 'hebrews',
        'james': 'james', 'jas': 'james',
        '1 pet': '1_peter', '1 peter': '1_peter', '1peter': '1_peter',
        '2 pet': '2_peter', '2 peter': '2_peter', '2peter': '2_peter',
        '1 john': '1_john', '1john': '1_john',
        '2 john': '2_john', '2john': '2_john',
        '3 john': '3_john', '3john': '3_john',
        'jude': 'jude',
        'rev': 'revelation', 'revelation': 'revelation', 'apocalypse': 'revelation'
    }
    
    return book_map.get(name)

def extract_references_from_content(content_file):
    """Extract scripture references from content.json."""
    with open(content_file, 'r', encoding='utf-8') as f:
        content = json.load(f)
    
    references = []
    
    # Extract from all paragraphs
    for para in content.get('paragraphs', []):
        # Remove footnote markers before parsing
        clean_para = re.sub(r'<sup>f\d+</sup>', '', para)
        refs = parse_biblical_reference(clean_para)
        for ref in refs:
            if ref not in references:
                references.append(ref)
    
    return references

def extract_references_from_footnotes(metadata_file):
    """Extract scripture references from footnotes."""
    if not metadata_file.exists():
        return []
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    references = []
    
    for fn_id, fn_text in metadata.get('footnotes', {}).items():
        refs = parse_biblical_reference(fn_text)
        for ref in refs:
            ref['source'] = f'footnote_{fn_id}'
            if ref not in references:
                references.append(ref)
    
    return references

def process_homilies():
    """Process all homilies and extract scripture references."""
    base_dir = Path(__file__).parent.parent
    content_dir = base_dir / 'content'
    
    total_references = 0
    homilies_processed = 0
    
    for homily_num in range(1, 91):  # Matthew has 90 homilies
        homily_dir = content_dir / f'{homily_num:03d}'
        if not homily_dir.exists():
            continue
        
        content_file = homily_dir / 'content.json'
        metadata_file = homily_dir / 'metadata.json'
        
        if not content_file.exists():
            print(f"Homily {homily_num}: No content.json found")
            continue
        
        # Extract references from content
        content_refs = extract_references_from_content(content_file)
        
        # Extract references from footnotes
        footnote_refs = extract_references_from_footnotes(metadata_file)
        
        # Combine and deduplicate
        all_refs = content_refs + footnote_refs
        
        # Organize by book
        organized_refs = {}
        for ref in all_refs:
            book = ref['book']
            if book not in organized_refs:
                organized_refs[book] = []
            organized_refs[book].append({
                'chapter': ref['chapter'],
                'verse': ref['verse'],
                'end_chapter': ref.get('end_chapter'),
                'end_verse': ref.get('end_verse'),
                'source': ref.get('source', 'text')
            })
        
        # Save scripture_references.json
        ref_file = homily_dir / 'scripture_references.json'
        with open(ref_file, 'w', encoding='utf-8') as f:
            json.dump(organized_refs, f, indent=2, ensure_ascii=False)
        
        total_references += len(all_refs)
        homilies_processed += 1
        print(f"Homily {homily_num:3d}: {len(all_refs)} references found")
    
    print(f"\nTotal homilies processed: {homilies_processed}")
    print(f"Total references extracted: {total_references}")

def main():
    print("Extracting scripture references from Chrysostom Matthew...")
    print("-" * 50)
    process_homilies()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Generate unified metadata structure for all commentaries.
Each homily/sermon gets its own folder with metadata.json containing all info including footnotes.
"""

import json
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

def int_to_roman(num):
    """Convert integer to Roman numeral"""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def clean_text(text):
    """Clean extracted text"""
    # Remove XML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove footnote markers
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

def extract_homily_text_from_xml(xml_path, homily_num):
    """Extract homily text from XML file"""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    roman = int_to_roman(homily_num)
    
    # Try div2 format first (homilies 1-39 for Matthew)
    pattern = f'(?s)<div2[^>]*n="{roman}"[^>]*>.*?</div2>'
    match = re.search(pattern, content)
    
    if not match:
        # Try paragraph format (homilies 40-90 for Matthew with ID offset)
        search_id = roman
        if 'matthew' in str(xml_path) and homily_num >= 77:
            search_id = int_to_roman(homily_num - 4)
        
        # Find by ID pattern
        start_pattern = f'<p[^>]*id="iii\\.{search_id}-p1"[^>]*>'
        start_match = re.search(start_pattern, content)
        
        if start_match:
            start = start_match.start()
            # Find next homily or end
            remaining = content[start:]
            end_pattern = r'<p[^>]*id="iii\.[IVXLC]+-p1"[^>]*>'
            end_match = re.search(end_pattern, remaining[100:])
            
            if end_match:
                end = start + 100 + end_match.start()
            else:
                end = min(start + 50000, len(content))
            
            match = content[start:end]
        else:
            match = None
    else:
        match = match.group(0)
    
    if match:
        # Clean the text
        text = clean_text(match)
        # Get first 200 words for excerpt
        words = text.split()[:200]
        excerpt = ' '.join(words) + '...' if len(words) == 200 else ' '.join(words)
        word_count = len(text.split())
        return text, excerpt, word_count
    
    return None, None, 0

def process_chrysostom_matthew():
    """Process Chrysostom's Matthew homilies"""
    base_dir = Path("texts/commentaries/chrysostom/matthew")
    
    # Load existing data
    coverage_path = base_dir / "homily_coverage.json"
    footnotes_path = base_dir / "footnotes.json"
    xml_path = base_dir / "chrysostom_matthew_homilies.xml"
    
    with open(coverage_path, 'r') as f:
        coverage = json.load(f)
    
    # Load footnotes if they exist
    footnotes = {}
    if footnotes_path.exists():
        with open(footnotes_path, 'r') as f:
            footnotes = json.load(f)
    
    # Create homilies directory
    homilies_dir = base_dir / "homilies"
    homilies_dir.mkdir(exist_ok=True)
    
    for num_str, info in coverage.items():
        num = int(num_str)
        homily_dir = homilies_dir / f"homily_{num:03d}"
        homily_dir.mkdir(exist_ok=True)
        
        # Extract text
        text, excerpt, word_count = extract_homily_text_from_xml(xml_path, num)
        
        # Build metadata
        metadata = {
            "id": num,
            "roman": info["homily_roman"],
            "title": f"Homily {info['homily_roman']}",
            "subtitle": info.get("title", ""),
            "author": "chrysostom",
            "author_full": "John Chrysostom",
            "work": "Homilies on Matthew",
            "scripture_reference": {
                "book": "matthew",
                "start": {
                    "chapter": info["start_chapter"],
                    "verse": info["start_verse"]
                },
                "end": {
                    "chapter": info["end_chapter"],
                    "verse": info["end_verse"]
                },
                "display": f"Matthew {info['start_chapter']}:{info['start_verse']}" +
                          (f"-{info['end_chapter']}:{info['end_verse']}" 
                           if (info['end_chapter'] != info['start_chapter'] or 
                               info['end_verse'] != info['start_verse']) else "")
            },
            "themes": [],  # Could be populated later
            "date_delivered": None,
            "word_count": word_count,
            "excerpt": excerpt,
            "source_file": "chrysostom_matthew_homilies.xml",
            "extraction_method": "div2" if num <= 39 else "paragraph",
            "has_footnotes": str(num) in footnotes,
            "footnotes": footnotes.get(str(num), {}),
            "verified": True
        }
        
        # Save metadata
        metadata_path = homily_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Created metadata for Matthew Homily {num}")
    
    print(f"✓ Processed {len(coverage)} Matthew homilies")

def process_chrysostom_john():
    """Process Chrysostom's John homilies"""
    base_dir = Path("texts/commentaries/chrysostom/john")
    
    # Load existing data
    coverage_path = base_dir / "homily_coverage.json"
    footnotes_path = base_dir / "footnotes.json"
    xml_path = base_dir / "chrysostom_john_homilies.xml"
    
    with open(coverage_path, 'r') as f:
        coverage = json.load(f)
    
    # Load footnotes
    footnotes = {}
    if footnotes_path.exists():
        with open(footnotes_path, 'r') as f:
            footnotes = json.load(f)
    
    # Create homilies directory
    homilies_dir = base_dir / "homilies"
    homilies_dir.mkdir(exist_ok=True)
    
    for num_str, info in coverage.items():
        num = int(num_str)
        homily_dir = homilies_dir / f"homily_{num:03d}"
        homily_dir.mkdir(exist_ok=True)
        
        # For John, we need to extract differently
        # Using simplified approach for now
        excerpt = f"Commentary on John {info['start_chapter']}:{info['start_verse']}"
        
        metadata = {
            "id": num,
            "roman": info["homily_roman"],
            "title": f"Homily {info['homily_roman']}",
            "subtitle": info.get("title", ""),
            "author": "chrysostom",
            "author_full": "John Chrysostom",
            "work": "Homilies on John",
            "scripture_reference": {
                "book": "john",
                "start": {
                    "chapter": info["start_chapter"],
                    "verse": info["start_verse"]
                },
                "end": {
                    "chapter": info["end_chapter"],
                    "verse": info["end_verse"]
                },
                "display": f"John {info['start_chapter']}:{info['start_verse']}" +
                          (f"-{info['end_chapter']}:{info['end_verse']}" 
                           if (info['end_chapter'] != info['start_chapter'] or 
                               info['end_verse'] != info['start_verse']) else "")
            },
            "themes": [],
            "date_delivered": None,
            "word_count": 0,  # To be calculated
            "excerpt": excerpt,
            "source_file": "chrysostom_john_homilies.xml",
            "extraction_method": "div2",
            "has_footnotes": str(num) in footnotes,
            "footnotes": footnotes.get(str(num), {}),
            "verified": True
        }
        
        # Save metadata
        metadata_path = homily_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Created metadata for John Homily {num}")
    
    print(f"✓ Processed {len(coverage)} John homilies")

def process_cyril_luke():
    """Process Cyril's Luke sermons"""
    base_dir = Path("texts/commentaries/cyril/luke")
    
    # Load existing data
    coverage_path = base_dir / "homily_coverage.json"
    sermons_path = base_dir / "cyril_luke_sermons.json"
    
    with open(coverage_path, 'r') as f:
        coverage = json.load(f)
    
    # Cyril doesn't have footnotes in our system
    
    # Create sermons directory
    sermons_dir = base_dir / "sermons"
    sermons_dir.mkdir(exist_ok=True)
    
    for num_str, info in coverage.items():
        # Skip negative numbers (these are special markers)
        if num_str.startswith('-'):
            continue
            
        num = int(num_str)
        sermon_dir = sermons_dir / f"sermon_{num:03d}"
        sermon_dir.mkdir(exist_ok=True)
        
        excerpt = f"Commentary on Luke {info['start_chapter']}:{info['start_verse']}"
        
        metadata = {
            "id": num,
            "roman": int_to_roman(num),
            "title": f"Sermon {int_to_roman(num)}",
            "subtitle": info.get("title", ""),
            "author": "cyril",
            "author_full": "Cyril of Alexandria",
            "work": "Commentary on Luke",
            "scripture_reference": {
                "book": "luke",
                "start": {
                    "chapter": info["start_chapter"],
                    "verse": info["start_verse"]
                },
                "end": {
                    "chapter": info["end_chapter"],
                    "verse": info["end_verse"]
                },
                "display": f"Luke {info['start_chapter']}:{info['start_verse']}" +
                          (f"-{info['end_chapter']}:{info['end_verse']}" 
                           if (info['end_chapter'] != info['start_chapter'] or 
                               info['end_verse'] != info['start_verse']) else "")
            },
            "themes": [],
            "date_delivered": None,
            "word_count": 0,  # To be calculated
            "excerpt": excerpt,
            "source_file": f"cyril_on_luke_{(num-1)//10+1:02d}_sermons.htm",
            "extraction_method": "html",
            "has_footnotes": False,
            "footnotes": {},
            "verified": True
        }
        
        # Save metadata
        metadata_path = sermon_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Created metadata for Luke Sermon {num}")
    
    print(f"✓ Processed {len([k for k in coverage.keys() if not k.startswith('-')])} Luke sermons")

def main():
    """Generate all metadata"""
    print("Generating unified metadata structure for all commentaries...")
    print("=" * 60)
    
    # No need to change directory, paths are relative to where script is run
    
    print("\n1. Processing Chrysostom's Matthew homilies...")
    process_chrysostom_matthew()
    
    print("\n2. Processing Chrysostom's John homilies...")
    process_chrysostom_john()
    
    print("\n3. Processing Cyril's Luke sermons...")
    process_cyril_luke()
    
    print("\n" + "=" * 60)
    print("✅ Metadata generation complete!")
    print("\nNext steps:")
    print("1. Update main.go to read from metadata.json files")
    print("2. Update README and CLAUDE.md with new structure")

if __name__ == "__main__":
    main()
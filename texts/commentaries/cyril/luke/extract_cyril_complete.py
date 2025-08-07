import os
import json
import re
from collections import defaultdict

def to_roman(num):
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def extract_sermon_info_from_file(filepath):
    """Extract sermon information from a single HTML file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sermons = []
    
    # Find all sermon entries in the table of contents
    sermon_pattern = r'<a href="#C\d+">Sermon[s]?\s+(\d+(?:\s*&amp;\s*\d+)?):?\s*Luke\s+([\d:\s]+(?:-[\d:\s]+)?)[^<]*</a>'
    matches = re.findall(sermon_pattern, content)
    
    for match in matches:
        sermon_nums, verse_ref = match
        
        # Handle multiple sermons (e.g., "8 & 9")
        if '&amp;' in sermon_nums:
            nums = [int(n.strip()) for n in sermon_nums.split('&amp;')]
        else:
            nums = [int(sermon_nums.strip())]
        
        # Parse verse reference
        verse_ref = verse_ref.strip().replace(' ', '')  # Remove any spaces
        verse_parts = verse_ref.split('-')
        if len(verse_parts) == 1:
            # Single verse or verse range within same chapter
            if ':' in verse_parts[0]:
                ch, v = verse_parts[0].split(':')
                start_ch = end_ch = int(ch)
                start_v = end_v = int(v)
            else:
                continue
        else:
            # Range of verses
            start_ref = verse_parts[0]
            end_ref = verse_parts[1]
            
            if ':' in start_ref:
                start_ch, start_v = start_ref.split(':')
                start_ch = int(start_ch)
                start_v = int(start_v)
            else:
                continue
                
            if ':' in end_ref:
                end_ch, end_v = end_ref.split(':')
                end_ch = int(end_ch)
                end_v = int(end_v)
            else:
                # End is just a verse number in the same chapter
                end_ch = start_ch
                end_v = int(end_ref)
        
        for num in nums:
            sermons.append({
                'number': num,
                'start_chapter': start_ch,
                'start_verse': start_v,
                'end_chapter': end_ch,
                'end_verse': end_v
            })
    
    return sermons

def create_complete_mapping():
    """Create the complete mapping of Cyril's sermons on Luke."""
    luke_dir = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke'
    all_sermons = []
    
    # Process each file
    files = sorted([f for f in os.listdir(luke_dir) if f.startswith('cyril_on_luke_') and f.endswith('.htm')])
    
    for filename in files:
        if 'intro' in filename:
            continue
            
        filepath = os.path.join(luke_dir, filename)
        print(f"Processing {filename}...")
        
        sermons = extract_sermon_info_from_file(filepath)
        all_sermons.extend(sermons)
    
    # Create homily coverage
    homily_coverage = {}
    for sermon in all_sermons:
        key = str(sermon['number'])
        homily_coverage[key] = {
            'homily_number': sermon['number'],
            'homily_roman': to_roman(sermon['number']),
            'start_chapter': sermon['start_chapter'],
            'start_verse': sermon['start_verse'],
            'end_chapter': sermon['end_chapter'],
            'end_verse': sermon['end_verse'],
            'title': f"Luke {sermon['start_chapter']}:{sermon['start_verse']}"
        }
    
    # Create verse to homilies mapping
    verse_to_homilies = defaultdict(list)
    
    for sermon in all_sermons:
        # Add entry for the starting verse
        key = f"{sermon['start_chapter']}:{sermon['start_verse']}"
        verse_to_homilies[key].append({
            'homily_number': sermon['number'],
            'homily_roman': to_roman(sermon['number']),
            'passage': f"Luke {sermon['start_chapter']}:{sermon['start_verse']}",
            'end': f"Luke {sermon['end_chapter']}:{sermon['end_verse']}"
        })
    
    return homily_coverage, dict(verse_to_homilies)

def extract_footnotes_from_files():
    """Extract footnotes from all HTML files."""
    luke_dir = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke'
    all_footnotes = {}
    
    files = sorted([f for f in os.listdir(luke_dir) if f.startswith('cyril_on_luke_') and f.endswith('.htm')])
    
    for filename in files:
        if 'intro' in filename:
            continue
            
        filepath = os.path.join(luke_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract footnotes
        footnote_pattern = r'<A HREF="#(\d+)"><SUP>\1</SUP></A>'
        footnote_refs = re.findall(footnote_pattern, content)
        
        # Extract footnote content
        for ref in footnote_refs:
            footnote_content_pattern = rf'<A NAME="{ref}"><SUP>{ref}</SUP></A>\s*([^<]+)'
            match = re.search(footnote_content_pattern, content)
            if match:
                all_footnotes[f"footnote_{ref}"] = match.group(1).strip()
    
    return all_footnotes

if __name__ == "__main__":
    print("Extracting Cyril's Luke commentary data...")
    
    # Create mappings
    homily_coverage, verse_to_homilies = create_complete_mapping()
    
    # Save homily coverage
    coverage_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/homily_coverage.json'
    with open(coverage_path, 'w', encoding='utf-8') as f:
        json.dump(homily_coverage, f, indent=2, ensure_ascii=False)
    print(f"Saved homily coverage for {len(homily_coverage)} sermons")
    
    # Save verse to homilies mapping
    verse_map_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/luke_verse_to_homilies.json'
    with open(verse_map_path, 'w', encoding='utf-8') as f:
        json.dump(verse_to_homilies, f, indent=2, ensure_ascii=False)
    print(f"Saved verse mapping for {len(verse_to_homilies)} verses")
    
    # Extract footnotes
    footnotes = extract_footnotes_from_files()
    footnotes_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/footnotes.json'
    with open(footnotes_path, 'w', encoding='utf-8') as f:
        json.dump(footnotes, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(footnotes)} footnotes")
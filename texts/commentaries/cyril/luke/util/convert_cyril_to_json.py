#!/usr/bin/env python3

import re
import os
import json
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import html
import roman

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    
    text = html.unescape(text)
    text = text.replace('\xa0', ' ')
    text = text.replace('\u2014', '—')
    text = text.replace('\u2013', '–')
    text = text.replace('\u2019', "'")
    text = text.replace('\u201c', '"')
    text = text.replace('\u201d', '"')
    text = text.replace('\u2018', "'")
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def extract_footnote_refs(text):
    """Extract footnote references and replace with markers"""
    footnote_pattern = r'<A HREF="#(\d+)"><SUP>(\d+)</SUP></A>'
    
    def replace_footnote(match):
        footnote_num = match.group(2)
        return f'<sup>f{footnote_num}</sup>'
    
    text = re.sub(footnote_pattern, replace_footnote, text, flags=re.IGNORECASE)
    return text

def roman_to_int(roman_num):
    """Convert Roman numeral to integer"""
    try:
        return roman.fromRoman(roman_num.upper())
    except:
        return None

def extract_sermon_from_anchor(soup, sermon_id):
    """Try various methods to find a sermon by its ID"""
    
    # Method 1: Direct anchor with name="C{id}"
    anchor = soup.find('a', {'name': f'C{sermon_id}'})
    if anchor:
        return anchor
    
    # Method 2: Within span with chapterno class
    chapter_spans = soup.find_all('span', {'class': 'chapterno'})
    for span in chapter_spans:
        anchor = span.find('a', {'name': f'C{sermon_id}'})
        if anchor:
            return anchor
    
    # Method 3: Look for SERMON patterns with Roman numerals
    for elem in soup.find_all(['h3', 'h2', 'a']):
        text = elem.get_text()
        # Match patterns like "SERMON XII", "Sermon XII", etc.
        match = re.search(r'SERMON\s+([IVXLC]+)', text, re.IGNORECASE)
        if match:
            sermon_num = roman_to_int(match.group(1))
            if sermon_num == sermon_id:
                # Check if this element has an anchor name
                if elem.name == 'a' and elem.get('name'):
                    return elem
                # Check children for anchors
                anchor = elem.find('a')
                if anchor:
                    return anchor
                return elem
    
    return None

def extract_sermon_content_robust(html_content, sermon_id):
    """Extract sermon content with robust parsing"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the sermon anchor - try multiple patterns
    anchor = None
    
    # Pattern 1: <A NAME="C{sermon_id}">
    anchor = soup.find('a', {'name': f'C{sermon_id}'})
    
    # Pattern 2: <a name="SERMON {roman}">
    if not anchor:
        try:
            roman_num = roman.toRoman(sermon_id)
            # Try various formats
            for pattern in [f'SERMON {roman_num}', f'SERMON {roman_num}.', f'SERMON{roman_num}']:
                anchor = soup.find('a', {'name': pattern})
                if anchor:
                    break
        except:
            pass
    
    # Pattern 3: Look for text containing "SERMON {roman}" in headings
    if not anchor:
        try:
            roman_num = roman.toRoman(sermon_id)
            for elem in soup.find_all(['h3', 'h2']):
                if f'SERMON {roman_num}' in elem.get_text().upper():
                    # Check if there's an anchor inside
                    inner_anchor = elem.find('a')
                    if inner_anchor:
                        anchor = inner_anchor
                    else:
                        anchor = elem
                    break
        except:
            pass
    
    if not anchor:
        return None
    
    # Get the parent element that contains the title
    title_elem = anchor.parent
    while title_elem and title_elem.name not in ['h3', 'h2', 'h1', 'blockquote']:
        title_elem = title_elem.parent
    
    # Extract title
    title_text = ""
    if title_elem and title_elem.name in ['h3', 'h2', 'h1']:
        title_text = clean_text(title_elem.get_text())
    
    # Parse title to get clean Roman numeral
    title_match = re.search(r'SERMON\s+([IVXLC]+)', title_text, re.IGNORECASE)
    if title_match:
        title = f"Sermon {title_match.group(1)}"
    else:
        # Try to convert sermon_id to Roman numeral
        try:
            title = f"Sermon {roman.toRoman(sermon_id)}"
        except:
            title = f"Sermon {sermon_id}"
    
    # Look for scripture reference in blockquote or near the title
    scripture_ref = ""
    current = title_elem if title_elem else anchor
    
    # Look for scripture reference in the next few elements
    for _ in range(10):
        current = current.find_next_sibling() if current else None
        if not current:
            break
        
        # Check if this is a blockquote with scripture reference
        if current.name == 'blockquote':
            text = current.get_text().strip()
            # Look for patterns like "2:8-18" or "Luke 2:8-18"
            match = re.search(r'(?:Luke\s+)?(\d+:\d+(?:-\d+(?::\d+)?)?)', text)
            if match:
                scripture_ref = match.group(0)
                break
        
        # Stop if we hit the next sermon
        if current.name in ['h3', 'h2'] and 'SERMON' in current.get_text().upper():
            break
    
    # Collect all paragraphs until the next sermon
    paragraphs = []
    current = anchor
    
    # Find the next sermon anchor to know where to stop
    next_sermon_id = sermon_id + 1
    next_anchor = None
    
    # Try to find next sermon anchor using various patterns
    # Pattern 1: C{id}
    next_anchor = soup.find('a', {'name': f'C{next_sermon_id}'})
    
    # Pattern 2: SERMON {roman}
    if not next_anchor:
        try:
            next_roman = roman.toRoman(next_sermon_id)
            for pattern in [f'SERMON {next_roman}', f'SERMON {next_roman}.', f'SERMON{next_roman}']:
                next_anchor = soup.find('a', {'name': pattern})
                if next_anchor:
                    break
        except:
            pass
    
    # If no next anchor, look for any higher numbered anchor
    if not next_anchor:
        for next_id in range(sermon_id + 1, sermon_id + 20):
            # Try C pattern
            test_anchor = soup.find('a', {'name': f'C{next_id}'})
            if test_anchor:
                next_anchor = test_anchor
                break
            # Try SERMON pattern
            try:
                test_roman = roman.toRoman(next_id)
                for pattern in [f'SERMON {test_roman}', f'SERMON {test_roman}.', f'SERMON{test_roman}']:
                    test_anchor = soup.find('a', {'name': pattern})
                    if test_anchor:
                        next_anchor = test_anchor
                        break
                if next_anchor:
                    break
            except:
                pass
    
    # Traverse elements and collect content
    while current:
        current = current.find_next(['p', 'blockquote', 'h3', 'h2', 'a'])
        if not current:
            break
        
        # Stop if we reached the next sermon
        if next_anchor and current == next_anchor:
            break
        
        # Stop if we hit a heading with the next sermon
        if current.name in ['h3', 'h2']:
            text = current.get_text().upper()
            if 'SERMON' in text and f'SERMON {roman.toRoman(sermon_id)}' not in text:
                # Check if this is a different sermon
                match = re.search(r'SERMON\s+([IVXLC]+)', text)
                if match:
                    try:
                        other_sermon = roman.fromRoman(match.group(1))
                        if other_sermon != sermon_id:
                            break
                    except:
                        pass
        
        # Check for anchor tags that might indicate next sermon
        if current.name == 'a' and current.get('name'):
            anchor_name = current.get('name')
            if anchor_name.startswith('C') and anchor_name != f'C{sermon_id}':
                try:
                    other_id = int(anchor_name[1:])
                    if other_id > sermon_id:
                        break
                except:
                    pass
        
        # Process content paragraphs
        if current.name == 'p':
            text = str(current)
            text = extract_footnote_refs(text)
            soup_p = BeautifulSoup(text, 'html.parser')
            clean = clean_text(soup_p.get_text())
            
            # Skip metadata, page markers, navigation, and footnote markers
            if clean and not any([
                clean.startswith(('[From', 'From the Syriac', 'From Mai', 'From Aubert')),
                re.match(r'^\|\d+\s*$', clean),
                re.match(r'^<A NAME="p\d+', clean),
                'Previous Page' in clean,
                'Table Of Contents' in clean,
                'Next Page' in clean,
                clean.startswith('cc.'),
                clean.startswith('c.'),
                re.match(r'^MS\.\s*\d+', clean)
            ]):
                paragraphs.append(clean)
        
        elif current.name == 'blockquote':
            # Process blockquotes (often contain scripture quotes)
            for elem in current.find_all(['p']):
                text = str(elem)
                text = extract_footnote_refs(text)
                soup_elem = BeautifulSoup(text, 'html.parser')
                clean = clean_text(soup_elem.get_text())
                if clean and not clean.startswith(('[From', 'From the Syriac')):
                    # Add scripture quotes with special formatting if needed
                    paragraphs.append(clean)
    
    if not paragraphs:
        return None
    
    return {
        'title': title,
        'subtitle': scripture_ref if scripture_ref else f"Luke {sermon_id}",
        'paragraphs': paragraphs
    }

def process_html_file(filepath, sermon_ranges):
    """Process HTML file and extract sermons"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    sermons = {}
    
    for sermon_id in sermon_ranges:
        sermon_data = extract_sermon_content_robust(content, sermon_id)
        if sermon_data and sermon_data['paragraphs']:
            sermons[sermon_id] = sermon_data
            print(f"    Extracted Sermon {sermon_id}: {len(sermon_data['paragraphs'])} paragraphs")
    
    return sermons

def main():
    base_dir = Path('/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke')
    source_dir = base_dir / 'source'
    content_dir = base_dir / 'content'
    
    # Map of HTML files to sermon IDs based on filenames and actual content
    file_mappings = {
        'cyril_on_luke_01_sermons_01_11.htm': range(1, 12),      # Sermons 1-11
        'cyril_on_luke_02_sermons_12_25.htm': range(12, 26),     # Sermons 12-25
        'cyril_on_luke_03_sermons_26_38.htm': range(26, 39),     # Sermons 26-38 (27,29,33-38 available)
        'cyril_on_luke_04_sermons_39_46.htm': range(39, 47),     # Sermons 39-46
        'cyril_on_luke_05_sermons_47_56.htm': range(47, 57),     # Sermons 47-56
        'cyril_on_luke_06_sermons_57_65.htm': range(57, 66),     # Sermons 57-65
        'cyril_on_luke_07_sermons_66_80.htm': range(66, 81),     # Sermons 66-80
        'cyril_on_luke_08_sermons_81_88.htm': range(81, 89),     # Sermons 81-88
        'cyril_on_luke_09_sermons_89_98.htm': range(89, 99),     # Sermons 89-98
        'cyril_on_luke_10_sermons_99_109.htm': range(99, 110),   # Sermons 99-109
        'cyril_on_luke_11_sermons_110_123.htm': range(110, 124), # Sermons 110-123
        'cyril_on_luke_12_sermons_124_134.htm': range(124, 135), # Sermons 124-134
        'cyril_on_luke_13_sermons_135_145.htm': range(135, 146), # Sermons 135-145
        'cyril_on_luke_14_sermons_146_156.htm': range(146, 157), # Sermons 146-156
    }
    
    all_sermons = {}
    
    for filename, sermon_range in file_mappings.items():
        filepath = source_dir / filename
        if filepath.exists():
            print(f"Processing {filename}...")
            sermons = process_html_file(filepath, sermon_range)
            all_sermons.update(sermons)
            print(f"  Total extracted: {len(sermons)} sermons")
        else:
            print(f"Warning: {filename} not found")
    
    # Create content directories and save JSON files
    created_count = 0
    for sermon_id, sermon_data in sorted(all_sermons.items()):
        sermon_dir = content_dir / f"{sermon_id:03d}"
        sermon_dir.mkdir(parents=True, exist_ok=True)
        
        json_path = sermon_dir / "content.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(sermon_data, f, indent=2, ensure_ascii=False)
        
        created_count += 1
        print(f"Created {json_path.name} - {sermon_data['title']}")
    
    print(f"\nTotal sermons converted: {created_count}")
    
    # List any gaps in sermon numbers
    sermon_ids = sorted(all_sermons.keys())
    expected = set(range(1, 157))
    missing = expected - set(sermon_ids)
    if missing:
        print(f"\nMissing sermons: {sorted(missing)}")

if __name__ == "__main__":
    main()
import os
import json
import re

def extract_footnotes_from_cyril_luke():
    """Extract all footnotes from Cyril's Luke commentary HTML files."""
    luke_dir = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke'
    all_footnotes = {}
    
    # Process each HTML file
    files = sorted([f for f in os.listdir(luke_dir) if f.startswith('cyril_on_luke_') and f.endswith('.htm')])
    
    for filename in files:
        if 'intro' in filename:
            continue
            
        filepath = os.path.join(luke_dir, filename)
        print(f"Processing {filename} for footnotes...")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all footnote references and their content
        # Pattern for footnote references: <A HREF="#1"><SUP>1</SUP></A>
        # Pattern for footnote content: <A NAME="1"><SUP>1</SUP></A> content...
        
        # First, find all footnote numbers
        footnote_refs = re.findall(r'<A HREF="#(\d+)"><SUP>\d+</SUP></A>', content)
        
        # Then extract the footnote content
        for ref_num in set(footnote_refs):
            # Look for the footnote definition at the bottom of the file
            # Pattern: <A NAME="number"></A>number. followed by the content until the next <p>
            pattern = rf'<A NAME="{ref_num}"></A>{ref_num}\.\s*([^<]+(?:<(?!p>|A NAME=)[^>]*>[^<]*</[^>]+>[^<]*)*)'
            match = re.search(pattern, content, re.DOTALL)
            
            if not match:
                # Try alternate pattern with &nbsp;
                pattern = rf'<A NAME="{ref_num}"></A>{ref_num}\.\&nbsp;([^<]+(?:<(?!p>|A NAME=)[^>]*>[^<]*</[^>]+>[^<]*)*)'
                match = re.search(pattern, content, re.DOTALL)
            
            if match:
                footnote_text = match.group(1).strip()
                # Clean up the text
                footnote_text = re.sub(r'\s+', ' ', footnote_text)
                footnote_text = re.sub(r'<[^>]+>', '', footnote_text)  # Remove HTML tags
                footnote_text = re.sub(r'&nbsp;', ' ', footnote_text)
                footnote_text = re.sub(r'&quot;', '"', footnote_text)
                footnote_text = re.sub(r'&amp;', '&', footnote_text)
                
                # Store with a unique key based on file and number
                footnote_key = f"{filename.replace('.htm', '')}_note_{ref_num}"
                all_footnotes[footnote_key] = {
                    'file': filename,
                    'number': int(ref_num),
                    'text': footnote_text.strip()
                }
    
    return all_footnotes

if __name__ == "__main__":
    print("Extracting footnotes from Cyril's Luke commentary...")
    
    footnotes = extract_footnotes_from_cyril_luke()
    
    # Save footnotes
    footnotes_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/footnotes.json'
    with open(footnotes_path, 'w', encoding='utf-8') as f:
        json.dump(footnotes, f, indent=2, ensure_ascii=False)
    
    print(f"Extracted and saved {len(footnotes)} footnotes")
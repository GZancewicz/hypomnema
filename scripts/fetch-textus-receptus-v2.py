import os
import urllib.request
import json
import time
import re

# Mapping from file names to folder names
book_mapping = {
    'MT.UTR': 'matthew',
    'MR.UTR': 'mark', 
    'LU.UTR': 'luke',
    'JOH.UTR': 'john',
    'AC.UTR': 'acts',
    'RO.UTR': 'romans',
    '1CO.UTR': '1corinthians',
    '2CO.UTR': '2corinthians',
    'GA.UTR': 'galatians',
    'EPH.UTR': 'ephesians',
    'PHP.UTR': 'philippians',
    'COL.UTR': 'colossians',
    '1TH.UTR': '1thessalonians',
    '2TH.UTR': '2thessalonians',
    '1TI.UTR': '1timothy',
    '2TI.UTR': '2timothy',
    'TIT.UTR': 'titus',
    'PHM.UTR': 'philemon',
    'HEB.UTR': 'hebrews',
    'JAS.UTR': 'james',
    '1PE.UTR': '1peter',
    '2PE.UTR': '2peter',
    '1JO.UTR': '1john',
    '2JO.UTR': '2john',
    '3JO.UTR': '3john',
    'JUDE.UTR': 'jude',
    'RE.UTR': 'revelation'
}

def get_file_list():
    """Get list of all files in the parsed directory"""
    url = "https://api.github.com/repos/byztxt/greektext-textus-receptus/contents/parsed"
    
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())
    
    files = []
    for item in data:
        if item['type'] == 'file' and item['name'].endswith('.UTR'):
            files.append({
                'name': item['name'],
                'download_url': item['download_url']
            })
    
    return files

def parse_utr_content(content):
    """Parse UTR format content into verses"""
    verses = {}
    current_verse = None
    current_text = []
    
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line starts with a verse reference (e.g., "1:1")
        match = re.match(r'^(\d+):(\d+)\s+(.+)', line)
        if match:
            # Save previous verse if exists
            if current_verse and current_text:
                verses[current_verse] = ' '.join(current_text)
            
            # Start new verse
            chapter = match.group(1)
            verse = match.group(2)
            current_verse = f"{chapter}:{verse}"
            
            # Extract Greek text (remove Strong's numbers and parsing info)
            text = match.group(3)
            # Remove Strong's numbers (e.g., 3972) and parsing tags (e.g., {N-NSM})
            text = re.sub(r'\s*\d+\s*\{[^}]+\}', '', text)
            current_text = [text]
        else:
            # Continuation of current verse
            if current_verse:
                # Remove Strong's numbers and parsing tags
                text = re.sub(r'\s*\d+\s*\{[^}]+\}', '', line)
                if text.strip():
                    current_text.append(text.strip())
    
    # Save last verse
    if current_verse and current_text:
        verses[current_verse] = ' '.join(current_text)
    
    return verses

def download_and_convert_book(file_info, output_dir):
    """Download and convert a single book"""
    filename = file_info['name']
    url = file_info['download_url']
    
    if filename not in book_mapping:
        print(f"  Skipping unknown file: {filename}")
        return False
    
    folder_name = book_mapping[filename]
    print(f"  Downloading {folder_name}...", end='', flush=True)
    
    try:
        # Download the file
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
        
        # Parse the content
        verses = parse_utr_content(content)
        
        if verses:
            # Create directory and save file
            book_dir = os.path.join(output_dir, folder_name)
            os.makedirs(book_dir, exist_ok=True)
            
            output_file = os.path.join(book_dir, f"{folder_name}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                # Sort verses by chapter and verse number
                sorted_verses = sorted(verses.items(), 
                                     key=lambda x: (int(x[0].split(':')[0]), 
                                                   int(x[0].split(':')[1])))
                
                for ref, text in sorted_verses:
                    f.write(f"{ref} {text}\n")
            
            print(f" ✓ ({len(verses)} verses)")
            return True
        else:
            print(" ✗ (no verses parsed)")
            return False
            
    except Exception as e:
        print(f" ✗ (error: {e})")
        return False

def main():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             'texts', 'scripture', 'greek', 'textus_receptus')
    
    print("Fetching Textus Receptus Greek New Testament...")
    print(f"Output directory: {output_dir}")
    
    # Get file list
    print("\nGetting file list from GitHub...")
    files = get_file_list()
    print(f"Found {len(files)} files")
    
    # Create NT book folders
    print("\nCreating folder structure...")
    for folder in book_mapping.values():
        os.makedirs(os.path.join(output_dir, folder), exist_ok=True)
    
    # Download and convert each book
    print("\nDownloading and converting books:")
    successful = 0
    
    for file_info in files:
        if download_and_convert_book(file_info, output_dir):
            successful += 1
        time.sleep(0.5)  # Be nice to GitHub API
    
    print(f"\nCompleted: {successful}/{len(book_mapping)} books downloaded successfully")

if __name__ == "__main__":
    main()
import os
import urllib.request
import json
import time

# Mapping from file names to folder names
book_mapping = {
    'MAT.UTR': 'matthew',
    'MAR.UTR': 'mark', 
    'LUK.UTR': 'luke',
    'JOH.UTR': 'john',
    'ACT.UTR': 'acts',
    'ROM.UTR': 'romans',
    '1CO.UTR': '1corinthians',
    '2CO.UTR': '2corinthians',
    'GAL.UTR': 'galatians',
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
    'JAM.UTR': 'james',
    '1PE.UTR': '1peter',
    '2PE.UTR': '2peter',
    '1JO.UTR': '1john',
    '2JO.UTR': '2john',
    '3JO.UTR': '3john',
    'JUD.UTR': 'jude',
    'REV.UTR': 'revelation'
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

def parse_utr_line(line):
    """Parse a UTR format line"""
    # UTR format: BookChapter:Verse\tGreekText\tParsing\tStrongs
    parts = line.strip().split('\t')
    if len(parts) >= 2:
        ref_parts = parts[0].split(':')
        if len(ref_parts) == 2:
            chapter_verse = ref_parts[1]
            if chapter_verse:
                # Extract chapter and verse
                # Format is like: MAT1:1 or MAT10:1
                book_chapter = ref_parts[0]
                # Remove book prefix (first 3 chars)
                chapter = book_chapter[3:]
                verse = chapter_verse
                greek_text = parts[1]
                
                return f"{chapter}:{verse} {greek_text}"
    
    return None

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
        lines = content.strip().split('\n')
        parsed_lines = []
        
        for line in lines:
            if line.strip():
                parsed = parse_utr_line(line)
                if parsed:
                    parsed_lines.append(parsed)
        
        if parsed_lines:
            # Create directory and save file
            book_dir = os.path.join(output_dir, folder_name)
            os.makedirs(book_dir, exist_ok=True)
            
            output_file = os.path.join(book_dir, f"{folder_name}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(parsed_lines))
            
            print(f" ✓ ({len(parsed_lines)} verses)")
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
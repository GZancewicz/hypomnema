import os
import json
import re
from html.parser import HTMLParser
from collections import defaultdict

class CyrilLukeParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sermons = []
        self.current_sermon = None
        self.in_sermon_title = False
        self.in_footnote = False
        self.current_text = []
        self.footnotes = {}
        self.capture_text = False
        self.in_blockquote = False
        self.current_verse_ref = None
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'a' and 'name' in attrs_dict and attrs_dict['name'].startswith('C'):
            sermon_id = attrs_dict['name']
            if sermon_id != 'misc':
                self.current_sermon = {
                    'id': sermon_id,
                    'content': [],
                    'verses': []
                }
                self.capture_text = True
        
        elif tag == 'blockquote':
            self.in_blockquote = True
            
        elif tag == 'sup' and self.capture_text:
            self.in_footnote = True
            
    def handle_endtag(self, tag):
        if tag == 'blockquote':
            self.in_blockquote = False
            
        elif tag == 'sup':
            self.in_footnote = False
            
    def handle_data(self, data):
        if self.capture_text and not self.in_footnote:
            text = data.strip()
            if text:
                if self.in_blockquote:
                    # Extract verse reference
                    verse_match = re.match(r'(\d+):(\d+(?:-\d+)?)\.\s*(.*)', text)
                    if verse_match:
                        chapter = int(verse_match.group(1))
                        verse_part = verse_match.group(2)
                        verse_text = verse_match.group(3)
                        
                        if '-' in verse_part:
                            start_v, end_v = verse_part.split('-')
                            self.current_verse_ref = {
                                'chapter': chapter,
                                'start_verse': int(start_v),
                                'end_verse': int(end_v),
                                'text': verse_text
                            }
                        else:
                            self.current_verse_ref = {
                                'chapter': chapter,
                                'start_verse': int(verse_part),
                                'end_verse': int(verse_part),
                                'text': verse_text
                            }
                        
                        if self.current_sermon:
                            self.current_sermon['verses'].append(self.current_verse_ref)
                
                if self.current_sermon:
                    self.current_sermon['content'].append(text)
                    
        # Check for sermon end
        if 'Sermon' in data and ':' in data and self.current_sermon:
            # Save previous sermon
            self.sermons.append(self.current_sermon)
            self.current_sermon = None
            self.capture_text = False

def parse_all_cyril_files():
    luke_dir = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke'
    all_sermons = []
    sermon_counter = 0
    
    # Process files in order
    for i in range(1, 15):
        filename = f'cyril_on_luke_{i:02d}_sermons_*.htm'
        # Find the actual file
        for file in os.listdir(luke_dir):
            if file.startswith(f'cyril_on_luke_{i:02d}_sermons'):
                filepath = os.path.join(luke_dir, file)
                print(f"Processing {file}...")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract sermon info from the title
                title_match = re.search(r'Sermons (\d+)-(\d+)\. \(Luke ([^)]+)\)', content)
                if not title_match:
                    # Try alternate format for single sermons
                    title_match = re.search(r'Sermon (\d+): Luke ([\d:]+(?:-[\d:]+)?)', content)
                
                parser = CyrilLukeParser()
                parser.feed(content)
                
                # Process extracted sermons
                for sermon_data in parser.sermons:
                    sermon_counter += 1
                    sermon = {
                        'number': sermon_counter,
                        'verses': sermon_data['verses'],
                        'content': '\n'.join(sermon_data['content'])
                    }
                    all_sermons.append(sermon)
    
    return all_sermons

def create_homily_coverage(sermons):
    coverage = {}
    
    for sermon in sermons:
        if sermon['verses']:
            # Get the first and last verse references
            first_verse = sermon['verses'][0]
            last_verse = sermon['verses'][-1]
            
            coverage[str(sermon['number'])] = {
                'homily_number': sermon['number'],
                'homily_roman': to_roman(sermon['number']),
                'start_chapter': first_verse['chapter'],
                'start_verse': first_verse['start_verse'],
                'end_chapter': last_verse['chapter'],
                'end_verse': last_verse['end_verse'],
                'title': f"Luke {first_verse['chapter']}:{first_verse['start_verse']}"
            }
    
    return coverage

def create_verse_to_homilies_mapping(coverage):
    verse_map = defaultdict(list)
    
    for homily_num, data in coverage.items():
        start_ch = data['start_chapter']
        start_v = data['start_verse']
        end_ch = data['end_chapter']
        end_v = data['end_verse']
        
        # Add mapping for the primary verse
        key = f"{start_ch}:{start_v}"
        verse_map[key].append({
            'homily_number': data['homily_number'],
            'homily_roman': data['homily_roman'],
            'passage': f"Luke {start_ch}:{start_v}",
            'end': f"Luke {end_ch}:{end_v}"
        })
    
    return dict(verse_map)

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

def extract_sermons_from_html():
    luke_dir = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke'
    homily_coverage = {}
    sermon_number = 0
    
    # Map of files to their sermon ranges
    file_sermon_map = [
        ('cyril_on_luke_01_sermons_01_11.htm', [(1, 2, 1, 7), (2, 2, 8, 18), (3, 2, 21, 24), 
                                                (4, 2, 25, 35), (5, 2, 40, 52), (6, 3, 1, 6),
                                                (7, 3, 7, 9), (8, 3, 10, 14), (9, 3, 10, 14),
                                                (10, 3, 15, 17), (11, 3, 21, 23)]),
        ('cyril_on_luke_02_sermons_12_25.htm', [(12, 4, 1, 13), (13, 4, 14, 21), (14, 4, 22, 37),
                                                (15, 4, 38, 41), (16, 4, 40, 44), (17, 5, 1, 11),
                                                (18, 5, 12, 15), (19, 5, 12, 16), (20, 5, 17, 32),
                                                (21, 5, 33, 39), (22, 6, 1, 5), (23, 6, 6, 11),
                                                (24, 6, 12, 16), (25, 6, 17, 19)]),
    ]
    
    # Continue with remaining files...
    # This is a simplified version - you would need to complete the mapping
    
    for filename, sermon_data in file_sermon_map:
        for sermon_num, start_ch, start_v, end_v in sermon_data:
            homily_coverage[str(sermon_num)] = {
                'homily_number': sermon_num,
                'homily_roman': to_roman(sermon_num),
                'start_chapter': start_ch,
                'start_verse': start_v,
                'end_chapter': start_ch,
                'end_verse': end_v,
                'title': f"Luke {start_ch}:{start_v}"
            }
    
    return homily_coverage

if __name__ == "__main__":
    # Extract homily coverage
    print("Extracting Cyril's Luke commentary data...")
    
    # For now, use manual extraction based on the HTML structure
    homily_coverage = extract_sermons_from_html()
    
    # Save homily coverage
    coverage_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/homily_coverage.json'
    with open(coverage_path, 'w', encoding='utf-8') as f:
        json.dump(homily_coverage, f, indent=2)
    print(f"Saved homily coverage to {coverage_path}")
    
    # Create verse to homilies mapping
    verse_map = create_verse_to_homilies_mapping(homily_coverage)
    verse_map_path = '/Users/gregzancewicz/Documents/Other/Projects/hypomnema/texts/commentaries/cyril/luke/luke_verse_to_homilies.json'
    with open(verse_map_path, 'w', encoding='utf-8') as f:
        json.dump(verse_map, f, indent=2)
    print(f"Saved verse mapping to {verse_map_path}")
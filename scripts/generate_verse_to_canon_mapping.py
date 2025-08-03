#!/usr/bin/env python3
"""Generate verse-to-canon mapping from SQLite database"""

import json
import sqlite3
from pathlib import Path

def to_roman(num):
    """Convert number to Roman numeral"""
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I']
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num

def main():
    print("Building verse-to-canon mapping from SQLite database...")
    
    db_path = Path('texts/reference/eusebian_canons/eusebian-canons.db')
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # This will hold verse -> canon.row mapping
    verse_mapping = {
        'matthew': {},
        'mark': {},
        'luke': {},
        'john': {}
    }
    
    # Define which gospels are in each canon
    canon_gospels = {
        1: ['MAT', 'MRK', 'LUK', 'JHN'],
        2: ['MAT', 'MRK', 'LUK'],
        3: ['MAT', 'LUK', 'JHN'],
        4: ['MAT', 'MRK', 'JHN'],
        5: ['MAT', 'LUK'],
        6: ['MAT', 'MRK'],
        7: ['MAT', 'JHN'],
        8: ['LUK', 'MRK'],
        9: ['LUK', 'JHN'],
        10: ['MAT'],
        11: ['MRK'],
        12: ['LUK'],
        13: ['JHN']
    }
    
    gospel_name_map = {
        'MAT': 'matthew',
        'MRK': 'mark',
        'LUK': 'luke',
        'JHN': 'john'
    }
    
    # Process each canon table
    for canon_num in range(1, 14):
        canon_roman = to_roman(canon_num)
        gospels = canon_gospels[canon_num]
        columns = ', '.join(gospels)
        
        # Get the canon table entries
        query = f"""
        SELECT rowid, {columns}
        FROM canon{canon_num}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            rowid = row[0]
            canon_ref = f"{canon_roman}.{rowid}"
            
            # Process each gospel in this canon
            for i, gospel_abbr in enumerate(gospels):
                section_num = row[i + 1]  # +1 because rowid is at index 0
                
                if section_num is not None:
                    # Get the verse reference for this section
                    verse_query = "SELECT reference FROM sections WHERE book=? AND sectionNumber=?"
                    cursor.execute(verse_query, (gospel_abbr, section_num))
                    result = cursor.fetchone()
                    if result:
                        verse_ref = result[0]
                        gospel_name = gospel_name_map[gospel_abbr]
                        
                        # Parse the verse reference to get chapter and verse
                        # Handle ranges like "3.10-16A"
                        if '-' in verse_ref:
                            start_verse = verse_ref.split('-')[0]
                        else:
                            start_verse = verse_ref
                        
                        # Remove any letter suffixes
                        import re
                        start_verse = re.sub(r'[A-Z]+$', '', start_verse)
                        
                        if '.' in start_verse:
                            parts = start_verse.split('.')
                            if len(parts) == 2:
                                chapter, verse = parts
                                # Add mapping for the starting verse
                                verse_key = f"{chapter}:{verse}"
                                verse_mapping[gospel_name][verse_key] = canon_ref
    
    conn.close()
    
    # Save to JSON
    output_file = Path('texts/reference/eusebian_canons/verse_to_canon.json')
    with open(output_file, 'w') as f:
        json.dump(verse_mapping, f, indent=2, sort_keys=True)
    
    print(f"Saved verse mappings to {output_file}")
    
    # Show sample
    print("\nSample mappings:")
    print("John 1:19 ->", verse_mapping['john'].get('1:19', 'Not found'))
    print("Matthew 3:3 ->", verse_mapping['matthew'].get('3:3', 'Not found'))

if __name__ == "__main__":
    main()
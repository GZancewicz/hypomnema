#!/usr/bin/env python3
"""Generate Eusebian Canon lookup table from SQLite database"""

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
    print("Building Eusebian Canon lookup table from SQLite database...")
    
    db_path = Path('texts/reference/eusebian_canons/eusebian-canons.db')
    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    canon_lookup = {}
    
    # Define which gospels are in each canon
    canon_gospels = {
        1: ['MAT', 'MRK', 'LUK', 'JHN'],  # All four
        2: ['MAT', 'MRK', 'LUK'],          # Synoptics
        3: ['MAT', 'LUK', 'JHN'],
        4: ['MAT', 'MRK', 'JHN'],
        5: ['MAT', 'LUK'],
        6: ['MAT', 'MRK'],
        7: ['MAT', 'JHN'],
        8: ['LUK', 'MRK'],                 # Note: order matters
        9: ['LUK', 'JHN'],
        10: ['MAT'],                       # Single gospel canons
        11: ['MRK'],
        12: ['LUK'],
        13: ['JHN']
    }
    
    # Process each canon table (1-13)
    for canon_num in range(1, 14):
        canon_roman = to_roman(canon_num)
        print(f"Processing Canon {canon_roman}...")
        
        # Build query based on which gospels are in this canon
        gospels = canon_gospels[canon_num]
        columns = ', '.join(gospels)
        
        # Get the canon table entries
        query = f"""
        SELECT rowid, {columns}
        FROM canon{canon_num}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        gospel_name_map = {
            'MAT': 'matthew',
            'MRK': 'mark',
            'LUK': 'luke',
            'JHN': 'john'
        }
        
        for row in rows:
            rowid = row[0]
            canon_key = f"{canon_roman}.{rowid}"
            canon_lookup[canon_key] = {}
            
            # Process each gospel in this canon
            for i, gospel_abbr in enumerate(gospels):
                section_num = row[i + 1]  # +1 because rowid is at index 0
                
                if section_num is not None:
                    verse_query = "SELECT reference FROM sections WHERE book=? AND sectionNumber=?"
                    cursor.execute(verse_query, (gospel_abbr, section_num))
                    result = cursor.fetchone()
                    if result:
                        gospel_name = gospel_name_map[gospel_abbr]
                        canon_lookup[canon_key][gospel_name] = result[0]
    
    conn.close()
    
    # Save to JSON
    output_file = Path('texts/reference/eusebian_canons/canon_lookup.json')
    with open(output_file, 'w') as f:
        json.dump(canon_lookup, f, indent=2, sort_keys=True)
    
    print(f"Saved {len(canon_lookup)} canon entries to {output_file}")
    
    # Show sample
    print("\nSample entries:")
    sample_keys = ['I.1', 'I.2', 'V.1', 'X.9', 'XIII.9']
    for key in sample_keys:
        if key in canon_lookup:
            print(f"\n{key}:")
            for gospel, verses in canon_lookup[key].items():
                print(f"  {gospel}: {verses}")

if __name__ == "__main__":
    main()
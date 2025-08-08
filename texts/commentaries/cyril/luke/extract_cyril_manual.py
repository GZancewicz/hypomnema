import json
import os

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

def create_cyril_luke_mapping():
    """Manually create the complete mapping based on the HTML files structure."""
    
    # Based on the file titles and content inspection
    sermon_data = [
        # File 1: cyril_on_luke_01_sermons_01_11.htm
        {'num': 1, 'start_ch': 2, 'start_v': 1, 'end_ch': 2, 'end_v': 7},
        {'num': 2, 'start_ch': 2, 'start_v': 8, 'end_ch': 2, 'end_v': 18},
        {'num': 3, 'start_ch': 2, 'start_v': 21, 'end_ch': 2, 'end_v': 24},
        {'num': 4, 'start_ch': 2, 'start_v': 25, 'end_ch': 2, 'end_v': 35},
        {'num': 5, 'start_ch': 2, 'start_v': 40, 'end_ch': 2, 'end_v': 52},
        {'num': 6, 'start_ch': 3, 'start_v': 1, 'end_ch': 3, 'end_v': 6},
        {'num': 7, 'start_ch': 3, 'start_v': 7, 'end_ch': 3, 'end_v': 9},
        {'num': 8, 'start_ch': 3, 'start_v': 10, 'end_ch': 3, 'end_v': 14},
        {'num': 9, 'start_ch': 3, 'start_v': 10, 'end_ch': 3, 'end_v': 14},
        {'num': 10, 'start_ch': 3, 'start_v': 15, 'end_ch': 3, 'end_v': 17},
        {'num': 11, 'start_ch': 3, 'start_v': 21, 'end_ch': 3, 'end_v': 23},
        
        # File 2: cyril_on_luke_02_sermons_12_25.htm (Luke 4:1-6:17)
        {'num': 12, 'start_ch': 4, 'start_v': 1, 'end_ch': 4, 'end_v': 13},
        {'num': 13, 'start_ch': 4, 'start_v': 14, 'end_ch': 4, 'end_v': 21},
        {'num': 14, 'start_ch': 4, 'start_v': 22, 'end_ch': 4, 'end_v': 37},
        {'num': 15, 'start_ch': 4, 'start_v': 38, 'end_ch': 4, 'end_v': 41},
        {'num': 16, 'start_ch': 4, 'start_v': 40, 'end_ch': 4, 'end_v': 44},
        {'num': 17, 'start_ch': 5, 'start_v': 1, 'end_ch': 5, 'end_v': 11},
        {'num': 18, 'start_ch': 5, 'start_v': 12, 'end_ch': 5, 'end_v': 15},
        {'num': 19, 'start_ch': 5, 'start_v': 12, 'end_ch': 5, 'end_v': 16},
        {'num': 20, 'start_ch': 5, 'start_v': 17, 'end_ch': 5, 'end_v': 32},
        {'num': 21, 'start_ch': 5, 'start_v': 33, 'end_ch': 5, 'end_v': 39},
        {'num': 22, 'start_ch': 6, 'start_v': 1, 'end_ch': 6, 'end_v': 5},
        {'num': 23, 'start_ch': 6, 'start_v': 6, 'end_ch': 6, 'end_v': 11},
        {'num': 24, 'start_ch': 6, 'start_v': 12, 'end_ch': 6, 'end_v': 16},
        {'num': 25, 'start_ch': 6, 'start_v': 17, 'end_ch': 6, 'end_v': 19},
        
        # Note: Sermon 26 appears to be missing
        
        # File 3: cyril_on_luke_03_sermons_27_38.htm (Luke 6:20-7:28)
        {'num': 27, 'start_ch': 6, 'start_v': 20, 'end_ch': 6, 'end_v': 26},
        {'num': 28, 'start_ch': 6, 'start_v': 27, 'end_ch': 6, 'end_v': 35},
        {'num': 29, 'start_ch': 6, 'start_v': 31, 'end_ch': 6, 'end_v': 31},
        {'num': 30, 'start_ch': 6, 'start_v': 37, 'end_ch': 6, 'end_v': 38},
        {'num': 31, 'start_ch': 6, 'start_v': 39, 'end_ch': 6, 'end_v': 42},
        {'num': 32, 'start_ch': 6, 'start_v': 43, 'end_ch': 6, 'end_v': 45},
        {'num': 33, 'start_ch': 6, 'start_v': 46, 'end_ch': 6, 'end_v': 49},
        {'num': 34, 'start_ch': 7, 'start_v': 1, 'end_ch': 7, 'end_v': 10},
        {'num': 35, 'start_ch': 7, 'start_v': 11, 'end_ch': 7, 'end_v': 17},
        {'num': 36, 'start_ch': 7, 'start_v': 18, 'end_ch': 7, 'end_v': 23},
        {'num': 37, 'start_ch': 7, 'start_v': 24, 'end_ch': 7, 'end_v': 28},
        {'num': 38, 'start_ch': 7, 'start_v': 24, 'end_ch': 7, 'end_v': 28},
        
        # File 4: cyril_on_luke_04_sermons_39_46.htm (Luke 7:31-8:56)
        {'num': 39, 'start_ch': 7, 'start_v': 31, 'end_ch': 7, 'end_v': 35},
        {'num': 40, 'start_ch': 7, 'start_v': 36, 'end_ch': 7, 'end_v': 50},
        {'num': 41, 'start_ch': 8, 'start_v': 1, 'end_ch': 8, 'end_v': 3},
        {'num': 42, 'start_ch': 8, 'start_v': 4, 'end_ch': 8, 'end_v': 15},
        {'num': 43, 'start_ch': 8, 'start_v': 16, 'end_ch': 8, 'end_v': 21},
        {'num': 44, 'start_ch': 8, 'start_v': 22, 'end_ch': 8, 'end_v': 25},
        {'num': 45, 'start_ch': 8, 'start_v': 26, 'end_ch': 8, 'end_v': 39},
        {'num': 46, 'start_ch': 8, 'start_v': 40, 'end_ch': 8, 'end_v': 56},
        
        # File 5: cyril_on_luke_05_sermons_47_56.htm (Luke 9:1-56)
        {'num': 47, 'start_ch': 9, 'start_v': 1, 'end_ch': 9, 'end_v': 6},
        {'num': 48, 'start_ch': 9, 'start_v': 10, 'end_ch': 9, 'end_v': 17},
        {'num': 49, 'start_ch': 9, 'start_v': 18, 'end_ch': 9, 'end_v': 22},
        {'num': 50, 'start_ch': 9, 'start_v': 23, 'end_ch': 9, 'end_v': 27},
        {'num': 51, 'start_ch': 9, 'start_v': 28, 'end_ch': 9, 'end_v': 36},
        {'num': 52, 'start_ch': 9, 'start_v': 37, 'end_ch': 9, 'end_v': 42},
        {'num': 53, 'start_ch': 9, 'start_v': 43, 'end_ch': 9, 'end_v': 45},
        {'num': 54, 'start_ch': 9, 'start_v': 46, 'end_ch': 9, 'end_v': 48},
        {'num': 55, 'start_ch': 9, 'start_v': 51, 'end_ch': 9, 'end_v': 56},
        {'num': 56, 'start_ch': 9, 'start_v': 51, 'end_ch': 9, 'end_v': 56},
        
        # File 6: cyril_on_luke_06_sermons_57_65.htm (Luke 9:57-10:21)
        {'num': 57, 'start_ch': 9, 'start_v': 57, 'end_ch': 9, 'end_v': 62},
        {'num': 58, 'start_ch': 10, 'start_v': 1, 'end_ch': 10, 'end_v': 7},
        {'num': 59, 'start_ch': 10, 'start_v': 8, 'end_ch': 10, 'end_v': 12},
        {'num': 60, 'start_ch': 10, 'start_v': 13, 'end_ch': 10, 'end_v': 15},
        {'num': 61, 'start_ch': 10, 'start_v': 16, 'end_ch': 10, 'end_v': 16},
        {'num': 62, 'start_ch': 10, 'start_v': 17, 'end_ch': 10, 'end_v': 20},
        {'num': 63, 'start_ch': 10, 'start_v': 21, 'end_ch': 10, 'end_v': 22},
        {'num': 64, 'start_ch': 10, 'start_v': 21, 'end_ch': 10, 'end_v': 22},
        {'num': 65, 'start_ch': 10, 'start_v': 21, 'end_ch': 10, 'end_v': 22},
        
        # File 7: cyril_on_luke_07_sermons_66_80.htm (Luke 10:22-11:18)
        {'num': 66, 'start_ch': 10, 'start_v': 23, 'end_ch': 10, 'end_v': 24},
        {'num': 67, 'start_ch': 10, 'start_v': 25, 'end_ch': 10, 'end_v': 37},
        {'num': 68, 'start_ch': 10, 'start_v': 38, 'end_ch': 10, 'end_v': 42},
        {'num': 69, 'start_ch': 11, 'start_v': 1, 'end_ch': 11, 'end_v': 4},
        {'num': 70, 'start_ch': 11, 'start_v': 5, 'end_ch': 11, 'end_v': 10},
        {'num': 71, 'start_ch': 11, 'start_v': 11, 'end_ch': 11, 'end_v': 13},
        {'num': 72, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 73, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 74, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 75, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 76, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 77, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 78, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 79, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        {'num': 80, 'start_ch': 11, 'start_v': 14, 'end_ch': 11, 'end_v': 18},
        
        # File 8: cyril_on_luke_08_sermons_81_88.htm (Luke 11:19-12:10)
        {'num': 81, 'start_ch': 11, 'start_v': 19, 'end_ch': 11, 'end_v': 28},
        {'num': 82, 'start_ch': 11, 'start_v': 29, 'end_ch': 11, 'end_v': 32},
        {'num': 83, 'start_ch': 11, 'start_v': 33, 'end_ch': 11, 'end_v': 36},
        {'num': 84, 'start_ch': 11, 'start_v': 37, 'end_ch': 11, 'end_v': 44},
        {'num': 85, 'start_ch': 11, 'start_v': 45, 'end_ch': 11, 'end_v': 54},
        {'num': 86, 'start_ch': 12, 'start_v': 1, 'end_ch': 12, 'end_v': 3},
        {'num': 87, 'start_ch': 12, 'start_v': 4, 'end_ch': 12, 'end_v': 7},
        {'num': 88, 'start_ch': 12, 'start_v': 8, 'end_ch': 12, 'end_v': 10},
        
        # File 9: cyril_on_luke_09_sermons_89_98.htm (Luke 12:13-13:9)
        {'num': 89, 'start_ch': 12, 'start_v': 13, 'end_ch': 12, 'end_v': 21},
        {'num': 90, 'start_ch': 12, 'start_v': 22, 'end_ch': 12, 'end_v': 31},
        {'num': 91, 'start_ch': 12, 'start_v': 32, 'end_ch': 12, 'end_v': 40},
        {'num': 92, 'start_ch': 12, 'start_v': 41, 'end_ch': 12, 'end_v': 48},
        {'num': 93, 'start_ch': 12, 'start_v': 49, 'end_ch': 12, 'end_v': 53},
        {'num': 94, 'start_ch': 12, 'start_v': 54, 'end_ch': 12, 'end_v': 59},
        {'num': 95, 'start_ch': 13, 'start_v': 1, 'end_ch': 13, 'end_v': 5},
        {'num': 96, 'start_ch': 13, 'start_v': 6, 'end_ch': 13, 'end_v': 9},
        {'num': 97, 'start_ch': 13, 'start_v': 6, 'end_ch': 13, 'end_v': 9},
        {'num': 98, 'start_ch': 13, 'start_v': 6, 'end_ch': 13, 'end_v': 9},
        
        # File 10: cyril_on_luke_10_sermons_99_109.htm (Luke 13:22-16:13)
        {'num': 99, 'start_ch': 13, 'start_v': 22, 'end_ch': 13, 'end_v': 30},
        {'num': 100, 'start_ch': 13, 'start_v': 31, 'end_ch': 13, 'end_v': 35},
        {'num': 101, 'start_ch': 14, 'start_v': 1, 'end_ch': 14, 'end_v': 6},
        {'num': 102, 'start_ch': 14, 'start_v': 7, 'end_ch': 14, 'end_v': 14},
        {'num': 103, 'start_ch': 14, 'start_v': 15, 'end_ch': 14, 'end_v': 24},
        {'num': 104, 'start_ch': 14, 'start_v': 25, 'end_ch': 14, 'end_v': 35},
        {'num': 105, 'start_ch': 15, 'start_v': 1, 'end_ch': 15, 'end_v': 10},
        {'num': 106, 'start_ch': 15, 'start_v': 11, 'end_ch': 15, 'end_v': 32},
        {'num': 107, 'start_ch': 16, 'start_v': 1, 'end_ch': 16, 'end_v': 13},
        {'num': 108, 'start_ch': 16, 'start_v': 1, 'end_ch': 16, 'end_v': 13},
        {'num': 109, 'start_ch': 16, 'start_v': 1, 'end_ch': 16, 'end_v': 13},
        
        # File 11: cyril_on_luke_11_sermons_110_123.htm (Luke 16:14-18:27)
        {'num': 110, 'start_ch': 16, 'start_v': 14, 'end_ch': 16, 'end_v': 18},
        {'num': 111, 'start_ch': 16, 'start_v': 19, 'end_ch': 16, 'end_v': 31},
        {'num': 112, 'start_ch': 17, 'start_v': 1, 'end_ch': 17, 'end_v': 4},
        {'num': 113, 'start_ch': 17, 'start_v': 5, 'end_ch': 17, 'end_v': 10},
        {'num': 114, 'start_ch': 17, 'start_v': 11, 'end_ch': 17, 'end_v': 19},
        {'num': 115, 'start_ch': 17, 'start_v': 20, 'end_ch': 17, 'end_v': 21},
        {'num': 116, 'start_ch': 17, 'start_v': 22, 'end_ch': 17, 'end_v': 37},
        {'num': 117, 'start_ch': 18, 'start_v': 1, 'end_ch': 18, 'end_v': 8},
        {'num': 118, 'start_ch': 18, 'start_v': 9, 'end_ch': 18, 'end_v': 14},
        {'num': 119, 'start_ch': 18, 'start_v': 15, 'end_ch': 18, 'end_v': 17},
        {'num': 120, 'start_ch': 18, 'start_v': 18, 'end_ch': 18, 'end_v': 27},
        {'num': 121, 'start_ch': 18, 'start_v': 18, 'end_ch': 18, 'end_v': 27},
        {'num': 122, 'start_ch': 18, 'start_v': 18, 'end_ch': 18, 'end_v': 27},
        {'num': 123, 'start_ch': 18, 'start_v': 18, 'end_ch': 18, 'end_v': 27},
        
        # File 12: cyril_on_luke_12_sermons_124_134.htm (Luke 18:28-20:18)
        {'num': 124, 'start_ch': 18, 'start_v': 28, 'end_ch': 18, 'end_v': 30},
        {'num': 125, 'start_ch': 18, 'start_v': 31, 'end_ch': 18, 'end_v': 34},
        {'num': 126, 'start_ch': 18, 'start_v': 35, 'end_ch': 18, 'end_v': 43},
        {'num': 127, 'start_ch': 19, 'start_v': 1, 'end_ch': 19, 'end_v': 10},
        {'num': 128, 'start_ch': 19, 'start_v': 11, 'end_ch': 19, 'end_v': 28},
        {'num': 129, 'start_ch': 19, 'start_v': 29, 'end_ch': 19, 'end_v': 40},
        {'num': 130, 'start_ch': 19, 'start_v': 41, 'end_ch': 19, 'end_v': 48},
        {'num': 131, 'start_ch': 20, 'start_v': 1, 'end_ch': 20, 'end_v': 8},
        {'num': 132, 'start_ch': 20, 'start_v': 9, 'end_ch': 20, 'end_v': 18},
        {'num': 133, 'start_ch': 20, 'start_v': 9, 'end_ch': 20, 'end_v': 18},
        {'num': 134, 'start_ch': 20, 'start_v': 9, 'end_ch': 20, 'end_v': 18},
        
        # File 13: cyril_on_luke_13_sermons_135_145.htm (Luke 20:19-22:38)
        {'num': 135, 'start_ch': 20, 'start_v': 19, 'end_ch': 20, 'end_v': 26},
        {'num': 136, 'start_ch': 20, 'start_v': 27, 'end_ch': 20, 'end_v': 40},
        {'num': 137, 'start_ch': 20, 'start_v': 41, 'end_ch': 20, 'end_v': 44},
        {'num': 138, 'start_ch': 20, 'start_v': 45, 'end_ch': 21, 'end_v': 4},
        {'num': 139, 'start_ch': 21, 'start_v': 5, 'end_ch': 21, 'end_v': 19},
        {'num': 140, 'start_ch': 21, 'start_v': 20, 'end_ch': 21, 'end_v': 24},
        {'num': 141, 'start_ch': 21, 'start_v': 25, 'end_ch': 21, 'end_v': 28},
        {'num': 142, 'start_ch': 21, 'start_v': 29, 'end_ch': 21, 'end_v': 38},
        {'num': 143, 'start_ch': 22, 'start_v': 1, 'end_ch': 22, 'end_v': 6},
        {'num': 144, 'start_ch': 22, 'start_v': 7, 'end_ch': 22, 'end_v': 23},
        {'num': 145, 'start_ch': 22, 'start_v': 24, 'end_ch': 22, 'end_v': 38},
        
        # File 14: cyril_on_luke_14_sermons_146_156.htm (Luke 22:39-24:45)
        {'num': 146, 'start_ch': 22, 'start_v': 39, 'end_ch': 22, 'end_v': 46},
        {'num': 147, 'start_ch': 22, 'start_v': 47, 'end_ch': 22, 'end_v': 53},
        {'num': 148, 'start_ch': 22, 'start_v': 54, 'end_ch': 22, 'end_v': 62},
        {'num': 149, 'start_ch': 22, 'start_v': 63, 'end_ch': 23, 'end_v': 12},
        {'num': 150, 'start_ch': 23, 'start_v': 13, 'end_ch': 23, 'end_v': 25},
        {'num': 151, 'start_ch': 23, 'start_v': 26, 'end_ch': 23, 'end_v': 31},
        {'num': 152, 'start_ch': 23, 'start_v': 32, 'end_ch': 23, 'end_v': 43},
        {'num': 153, 'start_ch': 23, 'start_v': 44, 'end_ch': 23, 'end_v': 56},
        {'num': 154, 'start_ch': 24, 'start_v': 1, 'end_ch': 24, 'end_v': 12},
        {'num': 155, 'start_ch': 24, 'start_v': 13, 'end_ch': 24, 'end_v': 35},
        {'num': 156, 'start_ch': 24, 'start_v': 36, 'end_ch': 24, 'end_v': 45},
    ]
    
    # Create homily coverage
    homily_coverage = {}
    for sermon in sermon_data:
        key = str(sermon['num'])
        homily_coverage[key] = {
            'homily_number': sermon['num'],
            'homily_roman': to_roman(sermon['num']),
            'start_chapter': sermon['start_ch'],
            'start_verse': sermon['start_v'],
            'end_chapter': sermon['end_ch'],
            'end_verse': sermon['end_v'],
            'title': f"Luke {sermon['start_ch']}:{sermon['start_v']}"
        }
    
    # Create verse to homilies mapping
    verse_to_homilies = {}
    
    for sermon in sermon_data:
        # Add entry for the starting verse
        key = f"{sermon['start_ch']}:{sermon['start_v']}"
        
        if key not in verse_to_homilies:
            verse_to_homilies[key] = []
            
        verse_to_homilies[key].append({
            'homily_number': sermon['num'],
            'homily_roman': to_roman(sermon['num']),
            'passage': f"Luke {sermon['start_ch']}:{sermon['start_v']}",
            'end': f"Luke {sermon['end_ch']}:{sermon['end_v']}"
        })
    
    return homily_coverage, verse_to_homilies

if __name__ == "__main__":
    print("Creating Cyril's Luke commentary mapping...")
    
    # Create mappings
    homily_coverage, verse_to_homilies = create_cyril_luke_mapping()
    
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
import os
import json

def main():
    books = [
        ('genesis', 50, 'Genesis'),
        ('exodos', 40, 'Exodus'),
        ('levitikon', 27, 'Leviticus'),
        ('arithmoi', 36, 'Numbers'),
        ('defteronomion', 34, 'Deuteronomy'),
        ('navi', 24, 'Joshua'),
        ('kritai', 21, 'Judges'),
        ('routh', 4, 'Ruth'),
        ('vasiliona', 31, '1 Samuel/Kings'),
        ('vasilionb', 24, '2 Samuel/Kings'),
        ('vasiliong', 22, '1 Kings'),
        ('vasiliond', 25, '2 Kings'),
        ('paralipomenona', 29, '1 Chronicles'),
        ('paralipomenonb', 36, '2 Chronicles'),
        ('esdrasa', 10, 'Ezra 1'),
        ('esdrasb', 10, 'Ezra 2'),
        ('neemias', 13, 'Nehemiah'),
        ('tovit', 14, 'Tobit'),
        ('ioudith', 16, 'Judith'),
        ('esthir', 16, 'Esther'),
        ('makkavaiona', 16, '1 Maccabees'),
        ('makkavaionb', 15, '2 Maccabees'),
        ('makkavaiong', 7, '3 Maccabees'),
        ('psalmoi', 151, 'Psalms'),
        ('iov', 42, 'Job'),
        ('parimiai', 31, 'Proverbs'),
        ('ekklhsiastis', 12, 'Ecclesiastes'),
        ('asma_asmaton', 8, 'Song of Songs'),
        ('sofia', 19, 'Wisdom'),
        ('sofia_sirah', 51, 'Sirach'),
        ('osie', 14, 'Hosea'),
        ('amos', 9, 'Amos'),
        ('miheas', 7, 'Micah'),
        ('iohl', 4, 'Joel'),
        ('ovdiou', 1, 'Obadiah'),
        ('ionas', 4, 'Jonah'),
        ('naoum', 3, 'Nahum'),
        ('amvakoum', 3, 'Habakkuk'),
        ('sofonias', 3, 'Zephaniah'),
        ('aggaios', 2, 'Haggai'),
        ('zaharias', 14, 'Zechariah'),
        ('malahias', 4, 'Malachi'),
        ('hsaias', 66, 'Isaiah'),
        ('ieremias', 52, 'Jeremiah'),
        ('varouh', 6, 'Baruch'),
        ('thrinoi', 5, 'Lamentations'),
        ('epistoli_ier', 1, 'Letter of Jeremiah'),
        ('iezekihl', 48, 'Ezekiel'),
        ('danihl', 14, 'Daniel'),
        ('makkavaiond', 18, '4 Maccabees')
    ]
    
    # Check which books have been fetched
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    completed = []
    remaining = []
    
    for folder, chapters, english in books:
        book_dir = os.path.join(base_dir, folder)
        if os.path.exists(book_dir) and os.listdir(book_dir):
            # Check if it has chapter folders
            subdirs = [d for d in os.listdir(book_dir) if os.path.isdir(os.path.join(book_dir, d))]
            if subdirs and subdirs[0].isdigit():
                completed.append((folder, chapters, english))
            else:
                remaining.append((folder, chapters, english))
        else:
            remaining.append((folder, chapters, english))
    
    print("Greek Septuagint Fetch Status")
    print("=" * 60)
    print(f"\nCompleted: {len(completed)} books")
    for folder, chapters, english in completed:
        print(f"  ✓ {english} ({folder})")
    
    print(f"\nRemaining: {len(remaining)} books")
    print("\nCommands to fetch remaining books:\n")
    
    for folder, chapters, english in remaining:
        print(f"# {english}")
        print(f"python scripts/fetch-septuagint-correct-pattern.py {folder} {chapters}")
        print()

if __name__ == "__main__":
    main()
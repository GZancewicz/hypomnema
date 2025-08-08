#\!/usr/bin/env python3
import re
from pathlib import Path

def fix_all_books():
    """Fix all NT books with complete text."""
    
    # Read the full text
    with open('hypomnema-server/kjv_full.txt', 'r') as f:
        full_text = f.read()
    
    books = [
        ("matthew", "The Gospel According to Saint Matthew", "The Gospel According to Saint Mark"),
        ("mark", "The Gospel According to Saint Mark", "The Gospel According to Saint Luke"),
        ("luke", "The Gospel According to Saint Luke", "The Gospel According to Saint John"),
        ("john", "The Gospel According to Saint John", "The Acts of the Apostles"),
        ("acts", "The Acts of the Apostles", "The Epistle of Paul"),
        ("romans", "The Epistle of Paul the Apostle to the Romans", "The First Epistle of Paul the Apostle to the Corinthians"),
        ("1corinthians", "The First Epistle of Paul the Apostle to the Corinthians", "The Second Epistle of Paul the Apostle to the Corinthians"),
        ("2corinthians", "The Second Epistle of Paul the Apostle to the Corinthians", "The Epistle of Paul the Apostle to the Galatians"),
        ("galatians", "The Epistle of Paul the Apostle to the Galatians", "The Epistle of Paul the Apostle to the Ephesians"),
        ("ephesians", "The Epistle of Paul the Apostle to the Ephesians", "The Epistle of Paul the Apostle to the Philippians"),
        ("philippians", "The Epistle of Paul the Apostle to the Philippians", "The Epistle of Paul the Apostle to the Colossians"),
        ("colossians", "The Epistle of Paul the Apostle to the Colossians", "The First Epistle of Paul the Apostle to the Thessalonians"),
        ("1thessalonians", "The First Epistle of Paul the Apostle to the Thessalonians", "The Second Epistle of Paul the Apostle to the Thessalonians"),
        ("2thessalonians", "The Second Epistle of Paul the Apostle to the Thessalonians", "The First Epistle of Paul the Apostle to Timothy"),
        ("1timothy", "The First Epistle of Paul the Apostle to Timothy", "The Second Epistle of Paul the Apostle to Timothy"),
        ("2timothy", "The Second Epistle of Paul the Apostle to Timothy", "The Epistle of Paul the Apostle to Titus"),
        ("titus", "The Epistle of Paul the Apostle to Titus", "The Epistle of Paul the Apostle to Philemon"),
        ("philemon", "The Epistle of Paul the Apostle to Philemon", "The Epistle of Paul the Apostle to the Hebrews"),
        ("hebrews", "The Epistle of Paul the Apostle to the Hebrews", "The Epistle of James"),
        ("james", "The Epistle of James", "The First Epistle of Peter"),
        ("1peter", "The First Epistle of Peter", "The Second Epistle of Peter"),
        ("2peter", "The Second Epistle of Peter", "The First Epistle of John"),
        ("1john", "The First Epistle of John", "The Second Epistle of John"),
        ("2john", "The Second Epistle of John", "The Third Epistle of John"),
        ("3john", "The Third Epistle of John", "The Epistle of Jude"),
        ("jude", "The Epistle of Jude", "The Revelation"),
        ("revelation", "The Revelation of Saint John the Divine", None)
    ]
    
    for book_id, start_marker, end_marker in books:
        print(f"Processing {book_id}...")
        
        # Find book start (skip TOC occurrence)
        first_idx = full_text.find(start_marker)
        if first_idx == -1:
            print(f"  Could not find {book_id}")
            continue
            
        # Find actual book start (second occurrence)
        book_start = full_text.find(start_marker, first_idx + len(start_marker))
        if book_start == -1:
            book_start = first_idx
        
        # Find book end
        if end_marker:
            book_end = full_text.find(end_marker, book_start + len(start_marker))
            if book_end == -1:
                book_text = full_text[book_start:]
            else:
                # Check for second occurrence of end marker
                second_end = full_text.find(end_marker, book_end + len(end_marker))
                if second_end != -1:
                    book_end = second_end
                book_text = full_text[book_start:book_end]
        else:
            book_text = full_text[book_start:]
        
        # Parse verses
        chapters = {}
        parts = re.split(r'(\d+:\d+)\s+', book_text)
        
        for i in range(1, len(parts), 2):
            if i+1 < len(parts):
                ref = parts[i]
                text = parts[i+1].strip()
                
                match = re.match(r'(\d+):(\d+)', ref)
                if match:
                    ch = int(match.group(1))
                    v = int(match.group(2))
                    
                    # Clean text
                    text = re.sub(r'\s+', ' ', text)
                    
                    if ch not in chapters:
                        chapters[ch] = {}
                    chapters[ch][v] = text
        
        # Save chapters
        base_path = Path("texts/scripture/new_testament/english/kjv")
        for chapter, verses in chapters.items():
            ch_dir = base_path / book_id / f"{chapter:02d}"
            ch_dir.mkdir(parents=True, exist_ok=True)
            
            ch_file = ch_dir / f"{book_id}_{chapter:02d}.txt"
            with open(ch_file, 'w') as f:
                for v_num in sorted(verses.keys()):
                    f.write(f"{chapter}:{v_num} {verses[v_num]}\n")
            
            print(f"  Saved chapter {chapter} ({len(verses)} verses)")
        
        print(f"  Total: {len(chapters)} chapters")

if __name__ == "__main__":
    fix_all_books()

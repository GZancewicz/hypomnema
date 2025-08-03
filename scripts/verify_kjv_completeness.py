#!/usr/bin/env python3
"""Verify all KJV chapters have content and expected verse counts"""

import os
import re
from pathlib import Path

# Expected chapter counts for NT books
CHAPTER_COUNTS = {
    'matthew': 28, 'mark': 16, 'luke': 24, 'john': 21,
    'acts': 28, 'romans': 16, '1corinthians': 16, '2corinthians': 13,
    'galatians': 6, 'ephesians': 6, 'philippians': 4, 'colossians': 4,
    '1thessalonians': 5, '2thessalonians': 3, '1timothy': 6, '2timothy': 4,
    'titus': 3, 'philemon': 1, 'hebrews': 13, 'james': 5,
    '1peter': 5, '2peter': 3, '1john': 5, '2john': 1,
    '3john': 1, 'jude': 1, 'revelation': 22
}

def check_chapter_content(book_name, chapter_num):
    """Check if chapter file exists and has verse content"""
    kjv_path = Path('texts/scripture/new_testament/english/kjv')
    chapter_file = kjv_path / book_name / f"{chapter_num:02d}" / f"{book_name}_{chapter_num:02d}.txt"
    
    if not chapter_file.exists():
        return False, "File missing"
    
    try:
        with open(chapter_file, 'r') as f:
            content = f.read().strip()
        
        if not content:
            return False, "Empty file"
        
        # Count verses (lines with format "1:1" or just "1")
        verse_lines = []
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Check for format "1:1 text" or "1 text"
            if ':' in line and line.split(':')[0].isdigit():
                verse_lines.append(line)
            elif line.split()[0].isdigit():
                verse_lines.append(line)
        verse_count = len(verse_lines)
        
        if verse_count == 0:
            return False, "No verses found"
        
        return True, f"{verse_count} verses"
    
    except Exception as e:
        return False, f"Error reading: {e}"

def main():
    print("Verifying KJV New Testament completeness...")
    print("=" * 60)
    
    total_books = 0
    complete_books = 0
    total_chapters = 0
    complete_chapters = 0
    issues = []
    
    for book_name, expected_chapters in CHAPTER_COUNTS.items():
        total_books += 1
        book_complete = True
        print(f"\n{book_name.upper()}: {expected_chapters} chapters")
        
        for chapter in range(1, expected_chapters + 1):
            total_chapters += 1
            is_complete, info = check_chapter_content(book_name, chapter)
            
            if is_complete:
                complete_chapters += 1
                print(f"  ✓ Chapter {chapter:2d}: {info}")
            else:
                book_complete = False
                print(f"  ✗ Chapter {chapter:2d}: {info}")
                issues.append(f"{book_name} {chapter}: {info}")
        
        if book_complete:
            complete_books += 1
            print(f"  → {book_name} COMPLETE")
        else:
            print(f"  → {book_name} INCOMPLETE")
    
    print(f"\n{'=' * 60}")
    print(f"SUMMARY:")
    print(f"Books: {complete_books}/{total_books} complete")
    print(f"Chapters: {complete_chapters}/{total_chapters} complete")
    
    if issues:
        print(f"\nISSUES FOUND ({len(issues)}):")
        for issue in issues:
            print(f"  • {issue}")
    else:
        print(f"\n🎉 ALL NEW TESTAMENT BOOKS AND CHAPTERS ARE COMPLETE!")

if __name__ == "__main__":
    main()
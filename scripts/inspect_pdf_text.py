#!/usr/bin/env python3
"""
Inspect PDF text extraction to understand formatting and improve paragraph detection.
"""

import sys
try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")
    sys.exit(1)

def inspect_pdf(pdf_path, start_page=50, num_pages=5):
    """Extract and display text from PDF to understand formatting."""
    
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        print(f"Total pages in PDF: {len(pdf_reader.pages)}")
        print(f"\nExtracting pages {start_page} to {start_page + num_pages}...\n")
        
        for page_num in range(start_page, min(start_page + num_pages, len(pdf_reader.pages))):
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            
            print(f"\n{'='*60}")
            print(f"PAGE {page_num + 1}")
            print(f"{'='*60}")
            
            # Show raw text with visible line breaks
            print("RAW TEXT:")
            print(repr(text[:500]))  # First 500 chars with escape sequences visible
            
            print("\n\nFORMATTED TEXT:")
            print(text[:1000])  # First 1000 chars formatted
            
            # Analyze paragraph patterns
            lines = text.split('\n')
            print(f"\n\nLINE ANALYSIS (first 20 lines):")
            for i, line in enumerate(lines[:20]):
                print(f"{i:3}: [{len(line):3}] {repr(line[:80])}")

if __name__ == "__main__":
    pdf_path = "../texts/commentaries/chrysostom/matthew/chrysostom_homilies_matthew.pdf"
    
    # You can change these to inspect different pages
    inspect_pdf(pdf_path, start_page=100, num_pages=2)
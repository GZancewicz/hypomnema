import os
import re

def clean_greek_text(text):
    """Remove all Strong's numbers and parsing tags from Greek text"""
    # First, ensure spaces before numbers
    text = re.sub(r'([^\s\d])(\d+)', r'\1 \2', text)
    # Remove patterns like "1510", "3588 {T-NSM}", "5707 {V-IAI-3S}"
    text = re.sub(r'\b\d+\s*(?:\{[^}]+\})?', '', text)
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_file(filepath):
    """Clean a single Greek text file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    for line in lines:
        if line.strip():
            # Split into reference and text
            parts = line.strip().split(' ', 1)
            if len(parts) == 2:
                reference = parts[0]
                greek_text = parts[1]
                cleaned_text = clean_greek_text(greek_text)
                if cleaned_text:
                    cleaned_lines.append(f"{reference} {cleaned_text}")
    
    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines) + '\n')
    
    return len(cleaned_lines)

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'textus_receptus')
    
    print("Cleaning Textus Receptus Greek text files...")
    
    total_cleaned = 0
    books_cleaned = 0
    
    # Process all book folders
    for book_folder in os.listdir(base_dir):
        book_path = os.path.join(base_dir, book_folder)
        if os.path.isdir(book_path):
            text_file = os.path.join(book_path, f"{book_folder}.txt")
            if os.path.exists(text_file):
                print(f"  Cleaning {book_folder}...", end='', flush=True)
                verses = clean_file(text_file)
                print(f" ✓ ({verses} verses)")
                total_cleaned += verses
                books_cleaned += 1
    
    print(f"\nCleaned {books_cleaned} books, {total_cleaned} total verses")

if __name__ == "__main__":
    main()
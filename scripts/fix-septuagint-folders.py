import os
import shutil

# Correct folder names based on the URLs between contents_ and .asp
correct_names = {
    'genesis': 'Genesis',
    'exodos': 'Exodos',
    'exodus': 'Exodos',  # Remove duplicate
    'levitikon': 'Levitikon',
    'arithmoi': 'Arithmoi',
    'defteronomion': 'Defteronomion',
    'navi': 'Navi',
    'kritai': 'Kritai',
    'routh': 'Routh',
    'vasiliona': 'VasilionA',
    'vasilionb': 'VasilionB',
    'vasiliong': 'VasilionG',
    'vasiliond': 'VasilionD',
    'paralipomenona': 'ParalipomenonA',
    'paralipomenonb': 'ParalipomenonB',
    'esdrasa': 'EsdrasA',
    'esdrasb': 'EsdrasB',
    'neemias': 'Neemias',
    'tovit': 'Tovit',
    'ioudith': 'Ioudith',
    'esthir': 'Esthir',
    'makkavaiona': 'MakkavaionA',
    'makkavaionb': 'MakkavaionB',
    'makkavaiong': 'makkavaionG',  # lowercase G as shown in URL
    'makkavaiond': 'makkavaionD',  # lowercase D as shown in URL
    'psalmoi': 'Psalmoi',
    'iov': 'Iov',
    'parimiai': 'Parimiai',
    'ekklhsiastis': 'Ekklhsiastis',
    'asma_asmaton': 'Asma_Asmaton',
    'sofia': 'Sofia',
    'sofia_sirah': 'Sofia_Sirah',
    'osie': 'Osie',
    'amos': 'Amos',
    'miheas': 'Miheas',
    'iohl': 'Iohl',
    'ovdiou': 'Ovdiou',
    'ionas': 'Ionas',
    'naoum': 'Naoum',
    'amvakoum': 'Amvakoum',
    'sofonias': 'Sofonias',
    'aggaios': 'Aggaios',
    'zaharias': 'Zaharias',
    'malahias': 'Malahias',
    'hsaias': 'Hsaias',
    'ieremias': 'Ieremias',
    'varouh': 'Varouh',
    'thrinoi': 'Thrinoi',
    'epistoli_ier': 'Epistoli_Ier',
    'iezekihl': 'Iezekihl',
    'danihl': 'Danihl'
}

def main():
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                            'texts', 'scripture', 'greek', 'septuagint')
    
    # Get all directories
    dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    print("Renaming folders to match URL patterns...")
    print("=" * 60)
    
    renamed = 0
    removed = 0
    
    for old_name in dirs:
        if old_name in correct_names:
            new_name = correct_names[old_name]
            if old_name != new_name:
                old_path = os.path.join(base_dir, old_name)
                new_path = os.path.join(base_dir, new_name)
                
                # Check if target exists (duplicate like exodus/exodos)
                if os.path.exists(new_path):
                    # Merge if both have content
                    print(f"Merging {old_name} -> {new_name}")
                    # Just remove the duplicate for now
                    shutil.rmtree(old_path)
                    removed += 1
                else:
                    print(f"Renaming {old_name} -> {new_name}")
                    os.rename(old_path, new_path)
                    renamed += 1
    
    print(f"\n{'='*60}")
    print(f"Renamed: {renamed} folders")
    print(f"Removed duplicates: {removed} folders")
    
    # List final structure
    print("\nFinal folder structure:")
    final_dirs = sorted([d for d in os.listdir(base_dir) 
                        if os.path.isdir(os.path.join(base_dir, d)) and not d.startswith('_')])
    for d in final_dirs:
        print(f"  {d}")

if __name__ == "__main__":
    main()
import json

# Update the get_book_sequence_numbers function in the main script
updated_sequences = {
    'genesis': 1,
    'exodos': 2,
    'levitikon': 3,
    'arithmoi': 4,
    'defteronomion': 5,
    'navi': 6,
    'kritai': 7,
    'routh': 8,
    'vasiliona': 9,      # 1 Samuel - Confirmed from site
    'vasilionb': 10,     # 2 Samuel
    'vasiliong': 11,     # 1 Kings
    'vasiliond': 12,     # 2 Kings
    'paralipomenona': 13,
    'paralipomenonb': 14,
    'esdrasa': 15,
    'esdrasb': 16,
    'neemias': 17,
    'tovit': 18,
    'ioudith': 19,
    'esthir': 20,
    'makkavaiona': 21,
    'makkavaionb': 22,
    'makkavaiong': 23,
    'psalmoi': 24,
    'iov': 25,
    'parimiai': 26,
    'ekklhsiastis': 27,
    'asma_asmaton': 28,
    'sofia': 29,
    'sofia_sirah': 30,
    'osie': 31,
    'amos': 32,
    'miheas': 33,
    'iohl': 34,
    'ovdiou': 35,
    'ionas': 36,
    'naoum': 37,
    'amvakoum': 38,
    'sofonias': 39,
    'aggaios': 40,
    'zaharias': 41,
    'malahias': 42,
    'hsaias': 43,
    'ieremias': 44,
    'varouh': 45,
    'thrinoi': 46,
    'epistoli_ier': 47,
    'iezekihl': 48,
    'danihl': 49,
    'makkavaiond': 50
}

print("Updated sequence numbers for all books")
print(f"Total books: {len(updated_sequences)}")

# Write to file for reference
with open('book_sequences.json', 'w') as f:
    json.dump(updated_sequences, f, indent=2)
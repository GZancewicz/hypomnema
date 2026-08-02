import re, json, os, html
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'texts/diatessaron/source/tatian_diatessaron.xml')
OUT = os.path.join(ROOT, 'texts/diatessaron')

BOOKS = {'Matt':'matthew','Mark':'mark','Luke':'luke','John':'john'}
ROMAN = ['','I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII','XIII','XIV','XV','XVI','XVII','XVIII','XIX','XX','XXI','XXII','XXIII','XXIV','XXV','XXVI','XXVII','XXVIII','XXIX','XXX','XXXI','XXXII','XXXIII','XXXIV','XXXV','XXXVI','XXXVII','XXXVIII','XXXIX','XL','XLI','XLII','XLIII','XLIV','XLV','XLVI','XLVII','XLVIII','XLIX','L','LI','LII','LIII','LIV','LV']

def strip_tags(s):
    s = re.sub(r'<pb\b[^>]*/?>', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()

MAX_CHAPTER = {'matthew': 28, 'mark': 16, 'luke': 24, 'john': 21}

# CCEL source typos: osisRef names a chapter the book does not have.
# Corrected from the surrounding citation sequence.
REF_FIXES = {
    ('mark', 21, 34): ('matthew', 21, 34),
}

def parse_note(note):
    """Return (book,chap,verse) if this is a pure citation note, else None."""
    refs = re.findall(r'osisRef="Bible:([^"]+)"', note)
    if len(refs) != 1:
        return None
    inner = re.sub(r'<scripRef.*?</scripRef>', '', note, flags=re.S)
    if len(strip_tags(inner).strip(' .')) >= 3:
        return None
    parts = refs[0].split('.')
    if len(parts) != 3 or parts[0] not in BOOKS:
        return None
    ref = (BOOKS[parts[0]], int(parts[1]), int(parts[2]))
    ref = REF_FIXES.get(ref, ref)
    if ref[1] > MAX_CHAPTER[ref[0]]:
        print(f'  WARNING: dropping out-of-range ref {ref[0]} {ref[1]}:{ref[2]}')
        return None
    return ref

data = open(SRC, encoding='utf-8').read()
i = data.find('<div2 id="iv.iii"'); j = data.find('<div2 id="iv.iv"')
body = data[i:j]

sec_re = re.compile(r'<div3[^>]*id="(iv\.iii\.[a-z]+)"[^>]*n="([IVXL]+)"[^>]*>')
marks = [(m.group(1), m.group(2), m.start(), m.end()) for m in sec_re.finditer(body)]

sections = []
verse_index = defaultdict(set)

for idx, (sid, roman, start, end) in enumerate(marks):
    stop = marks[idx+1][2] if idx+1 < len(marks) else len(body)
    chunk = body[end:stop]
    num = ROMAN.index(roman)

    # Split the section into stichs on the [n] markers, keeping preceding notes.
    tokens = re.split(r'(\[\d+\])', chunk)
    stichs = []
    pending_note_refs = []
    current = None

    def flush():
        global current
        if current and current['text']:
            stichs.append(current)
        current = None

    # Walk paragraph content: a note that immediately precedes text supplies its ref.
    parts = re.split(r'(<note\b.*?</note>|\[\d+\])', chunk, flags=re.S)
    cur_text = []
    cur_refs = []
    stich_no = None
    for p in parts:
        if not p:
            continue
        if p.startswith('<note'):
            r = parse_note(p)
            if r:
                cur_refs.append(r)
            continue
        m = re.fullmatch(r'\[(\d+)\]', p)
        if m:
            txt = strip_tags(''.join(cur_text))
            if txt and stich_no is not None:
                stichs.append({'n': stich_no, 'text': txt, 'refs': cur_refs})
            elif txt and stich_no is None and stichs:
                stichs[-1]['text'] += ' ' + txt
            cur_text, cur_refs = [], list(cur_refs)
            # refs collected before the marker belong to the upcoming stich
            stich_no = int(m.group(1))
            cur_refs = []
            continue
        cur_text.append(p)
    txt = strip_tags(''.join(cur_text))
    if txt and stich_no is not None:
        stichs.append({'n': stich_no, 'text': txt, 'refs': cur_refs})

    # Drop the "Section N." heading echo from the first stich
    for s in stichs:
        s['text'] = re.sub(r'^Section\s+[IVXL]+\.\s*', '', s['text']).strip()
    stichs = [s for s in stichs if s['text']]

    out_stichs = []
    for s in stichs:
        refs = []
        seen = set()
        for (b, c, v) in s['refs']:
            k = (b, c, v)
            if k in seen: continue
            seen.add(k)
            refs.append({'book': b, 'chapter': c, 'verse': v})
            verse_index[f'{b}.{c}.{v}'].add((num, s['n']))
        out_stichs.append({'n': s['n'], 'text': s['text'], 'refs': refs})

    all_books = []
    for s in out_stichs:
        for r in s['refs']:
            if r['book'] not in all_books:
                all_books.append(r['book'])

    sections.append({
        'number': num,
        'roman': roman,
        'id': sid,
        'title': f'Section {roman}',
        'books': all_books,
        'stich_count': len(out_stichs),
        'stichs': out_stichs,
    })

sections.sort(key=lambda s: s['number'])

os.makedirs(os.path.join(OUT, 'sections'), exist_ok=True)
for s in sections:
    with open(os.path.join(OUT, 'sections', f'section_{s["number"]:03d}.json'), 'w', encoding='utf-8') as f:
        json.dump(s, f, ensure_ascii=False, indent=1)

def book_ranges(stichs):
    per = {}
    for s in stichs:
        for r in s['refs']:
            per.setdefault(r['book'], set()).add((r['chapter'], r['verse']))
    out = {}
    for book, verses in per.items():
        runs = []
        for ch, vs in sorted(verses):
            if runs and runs[-1][0] == ch and vs == runs[-1][2] + 1:
                runs[-1][2] = vs
            elif runs and runs[-1][0] == ch and runs[-1][1] <= vs <= runs[-1][2]:
                continue
            else:
                runs.append([ch, vs, vs])
        out[book] = '; '.join(
            f'{ch}:{a}' if a == b else f'{ch}:{a}-{b}' for ch, a, b in runs)
    return out


def book_spans(stichs):
    """Condensed first-to-last span per book, for the index table."""
    per = {}
    for s in stichs:
        for r in s['refs']:
            per.setdefault(r['book'], set()).add((r['chapter'], r['verse']))
    out = {}
    for book, verses in per.items():
        vs = sorted(verses)
        (c1, v1), (c2, v2) = vs[0], vs[-1]
        if c1 == c2:
            out[book] = f'{c1}:{v1}' if v1 == v2 else f'{c1}:{v1}-{v2}'
        else:
            out[book] = f'{c1}:{v1}-{c2}:{v2}'
    return out

index = [{'number': s['number'], 'roman': s['roman'], 'title': s['title'],
          'books': s['books'], 'stich_count': s['stich_count'],
          'stich_start': s['stichs'][0]['n'] if s['stichs'] else 0,
          'stich_end': s['stichs'][-1]['n'] if s['stichs'] else 0,
          'book_ranges': book_ranges(s['stichs']),
          'book_spans': book_spans(s['stichs']),
          'excerpt': (s['stichs'][0]['text'][:160] + '…') if s['stichs'] else ''}
         for s in sections]
with open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8') as f:
    json.dump({'title': 'The Diatessaron of Tatian',
               'translator': 'Hope W. Hogg (ANF vol. 9, 1897)',
               'source': 'Arabic Diatessaron',
               'section_count': len(sections), 'sections': index}, f, ensure_ascii=False, indent=1)

vmap = {}
for k, v in verse_index.items():
    vmap[k] = [{'section': a, 'stich': b} for a, b in sorted(v)]
with open(os.path.join(OUT, 'verse_to_section.json'), 'w', encoding='utf-8') as f:
    json.dump(vmap, f, ensure_ascii=False, indent=1)

conflated = sum(1 for s in sections for st in s['stichs']
                if len({r['book'] for r in st['refs']}) > 1)
print(f'sections: {len(sections)}')
print(f'stichs:   {sum(s["stich_count"] for s in sections)}')
print(f'verses mapped: {len(vmap)}')
print(f'conflated stichs (>1 gospel): {conflated}')

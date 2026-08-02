import re, json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SRC = os.path.join(ROOT, 'texts/commentaries/ephraim/diatessaron/source/mosinger_1876_latin.txt')
OUT = os.path.join(ROOT, 'texts/commentaries/ephraim/diatessaron/sections')

# Ephraim's commentary on Diatessaron Section I (John 1:1-5 + Luke 1:5-79).
# Mosinger's own running heads bound it: it opens at "A principio erat Verbum
# (Joan. 1, 1-5)" and the next section begins at "Mense sexto (Luc. 1, 26-38)".
SECTIONS = {
    1: {'start': 781, 'end': 1519, 'refs': 'John 1:1-5; Luke 1:5-79'},
}

# OCR substitutions verified against the Mosinger scan. Applied to whole words
# only, so a correction never fires inside a word it was not checked against.
WORD_FIXES = {
    'hoe': 'hoc', 'Hoe': 'Hoc', 'haee': 'haec', 'Haee': 'Haec',
    'hae': 'haec', 'Hae': 'Haec', 'eujus': 'cujus',
    'neo': 'nec', 'seulo': 'saeculo', 'adseribi': 'adscribi',
    'aique': 'atque', 'Vietore': 'Victore', 'manuseriptum': 'manuscriptum',
    'Serip-': 'Scrip-', 'Seripturam': 'Scripturam', 'Serip': 'Scrip',
    'prineipio': 'principio', 'Ioax': 'Ioan', 'IoAx': 'Ioan',
    'Joax': 'Joan', 'JoAx': 'Joan', 'Marn': 'Matth', 'Lvc': 'Luc',
    'pronuneiatur': 'pronunciatur', 'loannes': 'Ioannes',
    'loannem': 'Ioannem', 'loannis': 'Ioannis', 'ilis': 'illis',
    'donee': 'donec', 'quamvis': 'quamvis', 'Sicut': 'Sicut',
    'explieat': 'explicat', 'signifieat': 'significat',
    'difficiliores': 'difficiliores', 'diffieiliores': 'difficiliores',
    'aecurateque': 'accurateque', 'Arme-': 'Arme-',
    'geniti-': 'geniti-', 'senectu-:': 'senectu-',
    'fili': 'filii', '8i': 'Si', '8ed': 'Sed',
}

# The scanner rendered « and » inconsistently; normalize the strays it produced.
QUOTE_FIXES = [(' ;', '»'), (' s,', '»,'), ('?;', '».'), ('!;', '».')]


def fix_ocr(s):
    out = []
    for tok in s.split(' '):
        bare = tok.strip('.,;:!?()»«')
        if bare in WORD_FIXES:
            tok = tok.replace(bare, WORD_FIXES[bare])
        out.append(tok)
    return ' '.join(out)


def is_artifact(line):
    """Page numbers and scan noise left between columns."""
    t = line.strip()
    if not t:
        return False
    if re.fullmatch(r'[0-9IVXLl\s.,\'"^*(){}|~-]{1,8}', t):
        return True
    if re.fullmatch(r'[A-Za-z0-9]{1,4}', t):
        return True
    return False


def is_page_break(line):
    """A page number ends the footnote block and resumes body text.

    The scan often garbles these (page 10 reads "Io9E"), so accept any short
    isolated run of digits and the letters they are commonly confused with.
    """
    t = line.strip()
    if re.fullmatch(r'[0-9]{1,3}', t) or re.fullmatch(r'[0-9]{1,3}\s+[0-9]{1,2}', t):
        return True
    return bool(re.fullmatch(r'[0-9IiloOSsEZB]{2,6}', t) and re.search(r'[0-9]', t))


FOOTNOTE_RE = re.compile(r'^(\d{1,2})\.\s+(.*)')
# A scripture citation in parentheses marks a new lemma in Mosinger's layout.
LEMMA_RE = re.compile(r'\((Joan|Ioan|Luc|Matth|Marc)\.[^)]*\)')


def parse_range(lines):
    """Split the raw column text into body paragraphs and numbered footnotes.

    Footnotes are set below a rule at the foot of each page; they always begin
    "N. " at line start and run until the next such marker or the page break.
    """
    body, notes = [], []
    mode, buf, cur = 'body', [], None

    def flush():
        nonlocal buf, cur
        text = ' '.join(buf).strip()
        if text:
            if mode == 'body':
                body.append(text)
            elif cur is not None:
                # Mosinger restarts footnote numbering on every page, so keep
                # these as an ordered list; a dict keyed by the printed number
                # would silently drop all but the last note of each number.
                notes.append((cur, text))
        buf = []

    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()

        # The page number sits below the footnote block, so it always returns
        # us to body text. Check before is_artifact, which would drop it.
        if is_page_break(line):
            flush()
            mode, cur = 'body', None
            continue

        if is_artifact(line) or not stripped:
            continue

        m = FOOTNOTE_RE.match(stripped)
        if m:
            flush()
            mode, cur = 'notes', m.group(1)
            buf = [m.group(2)]
            continue

        buf.append(stripped)

    flush()
    return body, notes


def dehyphenate(text):
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()


def split_lemmata(paragraphs):
    """Group body text into lemma units keyed by their scripture citation."""
    units, cur = [], {'heading': None, 'text': []}
    for para in paragraphs:
        m = LEMMA_RE.search(para)
        if m and cur['text']:
            units.append(cur)
            cur = {'heading': None, 'text': []}
        if m:
            cur['heading'] = m.group(0).strip('()')
        cur['text'].append(para)
    if cur['text']:
        units.append(cur)
    return units


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(SRC, encoding='utf-8') as f:
        all_lines = f.readlines()

    for num, spec in SECTIONS.items():
        chunk = all_lines[spec['start'] - 1:spec['end']]
        body, notes = parse_range(chunk)
        body = [fix_ocr(dehyphenate(p)) for p in body]

        # Renumber sequentially in reading order, starting at 1.
        renumbered = {
            str(i + 1): fix_ocr(dehyphenate(text))
            for i, (_, text) in enumerate(notes)
        }

        units = split_lemmata(body)
        data = {
            'section': num,
            'roman': 'I',
            'author': 'ephraim',
            'author_full': 'Ephraim the Syrian',
            'work': 'Commentary on the Diatessaron',
            'language': 'latin',
            'source': 'Moesinger, Evangelii concordantis expositio (1876)',
            'translator': 'J. B. Aucher, ed. G. Moesinger',
            'scripture_reference': spec['refs'],
            'lemmata': [
                {'heading': u['heading'], 'paragraphs': u['text']} for u in units
            ],
            'footnotes': renumbered,
            'has_footnotes': bool(renumbered),
            'paragraph_count': len(body),
        }

        path = os.path.join(OUT, f'section_{num:03d}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f'section {num}: {len(body)} paragraphs, {len(units)} lemmata, '
              f'{len(renumbered)} footnotes -> {path}')


if __name__ == '__main__':
    main()

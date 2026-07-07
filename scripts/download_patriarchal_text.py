import html
import os
import re
import time
import unicodedata
import urllib.request

BASE_URL = "http://onlinechapel.goarch.org/biblegreek/"
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "texts", "scripture", "new_testament", "greek", "patriarchal",
)

BOOKS = [
    (0, "Matt", "matthew"),
    (1, "Mark", "mark"),
    (2, "Luke", "luke"),
    (3, "John", "john"),
    (4, "Acts", "acts"),
    (5, "Rom", "romans"),
    (6, "1Cor", "1corinthians"),
    (7, "2Cor", "2corinthians"),
    (8, "Gal", "galatians"),
    (9, "Eph", "ephesians"),
    (10, "Phil", "philippians"),
    (11, "Col", "colossians"),
    (12, "1Thess", "1thessalonians"),
    (13, "2Thess", "2thessalonians"),
    (14, "1Tim", "1timothy"),
    (15, "2Tim", "2timothy"),
    (16, "Titus", "titus"),
    (17, "Phlm", "philemon"),
    (18, "Heb", "hebrews"),
    (19, "Jas", "james"),
    (20, "1Pet", "1peter"),
    (21, "2Pet", "2peter"),
    (22, "1John", "1john"),
    (23, "2John", "2john"),
    (24, "3John", "3john"),
    (25, "Jude", "jude"),
    (26, "Rev", "revelation"),
]

CHAPTER_RE = re.compile(
    r'<div type="chapter" osisID="[^".]+\.(\d+)"[^>]*>(.*?)(?=<div type="chapter"|</div>\s*</div>\s*<div style|$)',
    re.DOTALL,
)
VERSE_RE = re.compile(r'<span class="verse">\[(\d+)\]</span>')
TAG_RE = re.compile(r"<[^>]+>")


def fetch(book_id, abbrev):
    url = f"{BASE_URL}?id={book_id}&book={abbrev}&chapter=full"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def parse_chapter(chapter_html):
    verses = []
    parts = VERSE_RE.split(chapter_html)
    for i in range(1, len(parts), 2):
        verse_num = int(parts[i])
        text = TAG_RE.sub(" ", parts[i + 1])
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            verses.append((verse_num, text))
    return verses


REV_5_1_SPLITS = [
    "καὶ εἶδον ἄγγελον ἰσχυρὸν",
    "καὶ οὐδεὶς ἐδύνατο",
    "καὶ ἐγὼ ἔκλαιον",
    "καὶ εἷς ἐκ τῶν πρεσβυτέρων",
]


def strip_diacritics(s):
    chars = []
    positions = []
    for i, ch in enumerate(s):
        for d in unicodedata.normalize("NFD", ch):
            if not unicodedata.combining(d):
                chars.append(d)
                positions.append(i)
    return "".join(chars), positions


def find_plain(text, marker):
    stripped_text, positions = strip_diacritics(text)
    stripped_marker, _ = strip_diacritics(marker)
    idx = stripped_text.find(stripped_marker)
    if idx == -1:
        raise ValueError(f"marker not found: {marker}")
    return positions[idx]


def apply_fixes(name, lines):
    fixed = []
    for line in lines:
        ref, text = line.split(" ", 1)
        if name == "mark" and ref == "7:15" and text.endswith(" ["):
            text = text[:-2]
        elif name == "mark" and ref == "7:16":
            text = "[" + text
        elif name == "revelation" and ref == "5:1":
            verse = 1
            for marker in REV_5_1_SPLITS:
                idx = find_plain(text, marker)
                fixed.append(f"5:{verse} {text[:idx].strip()}")
                text = text[idx:]
                verse += 1
            ref = f"5:{verse}"
        fixed.append(f"{ref} {text}")
    return fixed


def main():
    for book_id, abbrev, name in BOOKS:
        page = fetch(book_id, abbrev)
        lines = []
        for match in CHAPTER_RE.finditer(page):
            chapter_num = int(match.group(1))
            for verse_num, text in parse_chapter(match.group(2)):
                lines.append(f"{chapter_num}:{verse_num} {text}")
        if not lines:
            print(f"WARNING: no verses parsed for {name}")
            continue
        lines = apply_fixes(name, lines)
        book_dir = os.path.join(OUTPUT_DIR, name)
        os.makedirs(book_dir, exist_ok=True)
        path = os.path.join(book_dir, f"{name}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        chapters = len({line.split(":")[0] for line in lines})
        print(f"{name}: {chapters} chapters, {len(lines)} verses")
        time.sleep(1)


if __name__ == "__main__":
    main()

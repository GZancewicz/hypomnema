#!/usr/bin/env python3
"""Build the Brenton Septuagint text tree from eBible USFM.

Follows the KJV New Testament conventions: plain text only, one line per verse
as "chapter:verse text", a per-chapter file under NN/, and a whole-book file.
"""
import re
import sys
from pathlib import Path

BRENTON = Path(__file__).resolve().parent.parent / "texts/scripture/old_testament/english/brenton"
SRC = BRENTON / "usfm/src"
OUT = BRENTON / "usfm"

BOOKS = {
    "GEN": "genesis", "EXO": "exodus", "LEV": "leviticus", "NUM": "numbers",
    "DEU": "deuteronomy", "JOS": "joshua", "JDG": "judges", "RUT": "ruth",
    "1SA": "1samuel", "2SA": "2samuel", "1KI": "1kings", "2KI": "2kings",
    "1CH": "1chronicles", "2CH": "2chronicles", "EZR": "ezra", "NEH": "nehemiah",
    "JOB": "job", "PSA": "psalms", "PRO": "proverbs", "ECC": "ecclesiastes",
    "SNG": "song_of_solomon", "ISA": "isaiah", "JER": "jeremiah",
    "LAM": "lamentations", "EZK": "ezekiel", "DAG": "daniel", "HOS": "hosea",
    "JOL": "joel", "AMO": "amos", "OBA": "obadiah", "JON": "jonah",
    "MIC": "micah", "NAM": "nahum", "HAB": "habakkuk", "ZEP": "zephaniah",
    "HAG": "haggai", "ZEC": "zechariah", "MAL": "malachi",
    "TOB": "tobit", "JDT": "judith", "ESG": "esther", "WIS": "wisdom",
    "SIR": "sirach", "BAR": "baruch", "LJE": "letter_of_jeremiah",
    "SUS": "susanna", "BEL": "bel_and_the_dragon", "1MA": "1maccabees",
    "2MA": "2maccabees", "1ES": "1esdras", "MAN": "prayer_of_manasseh",
    "3MA": "3maccabees", "4MA": "4maccabees",
}

# Notes carry their own content between the opening and closing marker; the whole
# span must go, not just the markers.
NOTE_SPAN = re.compile(r"\\(f|x)\s.*?\\\1\*", re.DOTALL)
CHAR_MARKER = re.compile(r"\\\+?[a-z]+[0-9]*\*?")
WS = re.compile(r"\s+")


def clean(text):
    text = NOTE_SPAN.sub("", text)
    text = CHAR_MARKER.sub("", text)
    text = WS.sub(" ", text)
    return text.strip()


def parse(path):
    """Return (book_code, {chapter: {verse: text}}) preserving encounter order."""
    raw = path.read_text(encoding="utf-8-sig")
    code = None
    m = re.search(r"\\id\s+(\S+)", raw)
    if m:
        code = m.group(1)

    # Join the verse's continuation lines, then split on \v and \c.
    chapters, chapter, verse, buf = {}, None, None, []

    def flush():
        if chapter is not None and verse is not None:
            text = clean(" ".join(buf))
            if text:
                chapters.setdefault(chapter, {})[verse] = text

    for line in raw.splitlines():
        cm = re.match(r"\\c\s+(\d+)", line)
        if cm:
            flush()
            chapter, verse, buf = int(cm.group(1)), None, []
            chapters.setdefault(chapter, {})
            continue
        vm = re.match(r"\\v\s+(\d+)\s*(.*)", line)
        if vm:
            flush()
            verse, buf = int(vm.group(1)), [vm.group(2)]
            continue
        if re.match(r"\\(id|h|toc\d|mt\d|is\d|ip|im|ib|cl|ie)\b", line):
            continue
        if verse is not None:
            buf.append(re.sub(r"^\\[a-z]+\d*\s*", "", line))
    flush()
    return code, chapters


def main():
    written = []
    for path in sorted(SRC.glob("*.usfm")):
        code, chapters = parse(path)
        if code not in BOOKS:
            continue
        name = BOOKS[code]
        book_dir = OUT / name
        book_dir.mkdir(parents=True, exist_ok=True)

        book_lines, nverses = [], 0
        for ch in sorted(chapters):
            verses = chapters[ch]
            if not verses:
                continue
            lines = [f"{ch}:{v} {verses[v]}" for v in sorted(verses)]
            cdir = book_dir / f"{ch:02d}"
            cdir.mkdir(exist_ok=True)
            (cdir / f"{name}_{ch:02d}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
            book_lines.extend(lines)
            nverses += len(lines)
        (book_dir / f"{name}.txt").write_text("\n".join(book_lines) + "\n", encoding="utf-8")
        written.append((name, code, len(chapters), nverses))

    for name, code, nch, nv in written:
        print(f"{name:22} {code:4} {nch:4} chapters {nv:6} verses")
    print(f"\n{len(written)} books, {sum(w[3] for w in written)} verses")


if __name__ == "__main__":
    main()

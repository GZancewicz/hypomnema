#!/usr/bin/env python3
"""Search the KJV New Testament for a string and return matching verse locations as JSON.

Case-insensitive by default. Whole-word matching by default (so "art" does not match
"heart"); pass --substring for raw substring matching or --regex to treat the query as a
regular expression.

Output: JSON array of {"book","chapter","verse"} (canonical NT order), e.g.
    [{"book": "Matthew", "chapter": 4, "verse": 18}, ...]
"""

import argparse
import json
import re
import sys
from pathlib import Path

BOOKS = [
    ("matthew", "Matthew"),
    ("mark", "Mark"),
    ("luke", "Luke"),
    ("john", "John"),
    ("acts", "Acts"),
    ("romans", "Romans"),
    ("1corinthians", "1 Corinthians"),
    ("2corinthians", "2 Corinthians"),
    ("galatians", "Galatians"),
    ("ephesians", "Ephesians"),
    ("philippians", "Philippians"),
    ("colossians", "Colossians"),
    ("1thessalonians", "1 Thessalonians"),
    ("2thessalonians", "2 Thessalonians"),
    ("1timothy", "1 Timothy"),
    ("2timothy", "2 Timothy"),
    ("titus", "Titus"),
    ("philemon", "Philemon"),
    ("hebrews", "Hebrews"),
    ("james", "James"),
    ("1peter", "1 Peter"),
    ("2peter", "2 Peter"),
    ("1john", "1 John"),
    ("2john", "2 John"),
    ("3john", "3 John"),
    ("jude", "Jude"),
    ("revelation", "Revelation"),
]
DISPLAY = dict(BOOKS)
ALIASES = {name.lower().replace(" ", ""): slug for slug, name in BOOKS}
ALIASES.update({slug: slug for slug, _ in BOOKS})

LINE_RE = re.compile(r"^(\d+):(\d+)\s+(.*)$")


def find_kjv_root(start: Path) -> Path:
    target = Path("texts/scripture/new_testament/english/kjv")
    for base in [start, *start.parents]:
        candidate = base / target
        if candidate.is_dir():
            return candidate
    sys.exit(f"error: could not locate {target} above {start}")


def build_pattern(query: str, substring: bool, regex: bool) -> re.Pattern:
    if regex:
        body = query
    elif substring:
        body = re.escape(query)
    else:
        body = r"(?<!\w)" + re.escape(query) + r"(?!\w)"
    try:
        return re.compile(body, re.IGNORECASE)
    except re.error as exc:
        sys.exit(f"error: invalid regex: {exc}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Search the KJV New Testament.")
    ap.add_argument("query", help="string to search for (case-insensitive)")
    ap.add_argument("--substring", action="store_true",
                    help="match anywhere in a word, not just whole words")
    ap.add_argument("--regex", action="store_true",
                    help="treat query as a regular expression")
    ap.add_argument("--book", help="limit to one book (e.g. 'john', '1 Corinthians')")
    ap.add_argument("--with-text", action="store_true",
                    help="include the verse text in each result")
    ap.add_argument("--count", action="store_true",
                    help="print only the number of matching verses")
    ap.add_argument("--root", help="path to the kjv directory (auto-detected by default)")
    args = ap.parse_args()

    if args.root:
        root = Path(args.root)
        if not root.is_dir():
            sys.exit(f"error: --root not a directory: {root}")
    else:
        root = find_kjv_root(Path(__file__).resolve().parent)

    if args.book:
        key = args.book.lower().replace(" ", "")
        if key not in ALIASES:
            sys.exit(f"error: unknown book '{args.book}'")
        books = [(ALIASES[key], DISPLAY[ALIASES[key]])]
    else:
        books = BOOKS

    pattern = build_pattern(args.query, args.substring, args.regex)
    results = []

    for slug, display in books:
        book_dir = root / slug
        if not book_dir.is_dir():
            continue
        for chap_dir in sorted(book_dir.iterdir()):
            if not chap_dir.is_dir():
                continue
            chap_file = chap_dir / f"{slug}_{chap_dir.name}.txt"
            if not chap_file.is_file():
                continue
            for line in chap_file.read_text(encoding="utf-8").splitlines():
                m = LINE_RE.match(line)
                if not m:
                    continue
                chapter, verse, text = int(m.group(1)), int(m.group(2)), m.group(3)
                if pattern.search(text):
                    entry = {"book": display, "chapter": chapter, "verse": verse}
                    if args.with_text:
                        entry["text"] = text
                    results.append(entry)

    if args.count:
        print(len(results))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

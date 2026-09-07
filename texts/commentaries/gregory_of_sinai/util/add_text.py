#!/usr/bin/env python3
"""Register one numbered text of St Gregory of Sinai's *On Commandments and Doctrines*
(Philokalia vol. 4) as a Gospel citation.

Writes texts/NNN.md and upserts the matching entry in coverage.json.

    python3 texts/commentaries/gregory_of_sinai/util/add_text.py \
        --id 15 --verse "matthew 3:3" --text-file /path/to/015.md

    python3 texts/commentaries/gregory_of_sinai/util/add_text.py \
        --id 27 --verse "mt 5:8" --end "mt 5:9" --text-file /path/to/027.md --dry-run
"""

import argparse
import json
import os
import re
import sys

AUTHOR_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK_DIR = os.path.join(AUTHOR_DIR, "On Commandments and Doctrines")
COVERAGE = os.path.join(WORK_DIR, "coverage.json")
TEXTS = os.path.join(WORK_DIR, "texts")
KJV = os.path.normpath(os.path.join(AUTHOR_DIR, "..", "..", "scripture", "new_testament", "english", "kjv"))

MAX_ID = 137

BOOKS = {
    "matthew": "matthew", "matt": "matthew", "mt": "matthew",
    "mark": "mark", "mk": "mark",
    "luke": "luke", "lk": "luke",
    "john": "john", "jn": "john",
}

REF_RE = re.compile(r"^\s*([1-3]?\s*[A-Za-z]+)\.?\s+(\d+)\s*[:.]\s*(\d+)\s*$")


def parse_ref(s):
    m = REF_RE.match(s)
    if not m:
        sys.exit(f"Cannot parse verse reference: {s!r} (expected e.g. 'matthew 3:3')")
    book = BOOKS.get(m.group(1).lower().replace(" ", ""))
    if book is None:
        sys.exit(f"Not a Gospel: {m.group(1)!r} (only Matthew, Mark, Luke, John are supported)")
    return book, int(m.group(2)), int(m.group(3))


def verse_exists(book, chapter, verse):
    path = os.path.join(KJV, book, f"{chapter:02d}", f"{book}_{chapter:02d}.txt")
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    return re.search(rf"^{chapter}:{verse}\b", text, flags=re.M) is not None


def load_coverage():
    if not os.path.exists(COVERAGE):
        return {"commentary": "On Commandments and Doctrines", "total_homilies": 0, "homilies": []}
    return json.load(open(COVERAGE, encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", type=int, required=True, help="text number within the work (1-137)")
    ap.add_argument("--verse", required=True, help="start verse, e.g. 'matthew 3:3'")
    ap.add_argument("--end", help="end verse (default: same as --verse)")
    ap.add_argument("--text-file", help="file holding the transcribed text (markdown, *emphasis* only)")
    ap.add_argument("--dry-run", action="store_true", help="print the summary, write nothing")
    args = ap.parse_args()

    if not 1 <= args.id <= MAX_ID:
        sys.exit(f"--id must be 1..{MAX_ID} (On Commandments and Doctrines has {MAX_ID} texts)")

    sbook, sch, sv = parse_ref(args.verse)
    ebook, ech, ev = parse_ref(args.end) if args.end else (sbook, sch, sv)
    if ebook != sbook:
        sys.exit("--verse and --end must be in the same Gospel")
    if (ech, ev) < (sch, sv):
        sys.exit("--end precedes --verse")
    for ch, v in ((sch, sv), (ech, ev)):
        if not verse_exists(sbook, ch, v):
            sys.exit(f"{sbook} {ch}:{v} is not a KJV verse")

    text = None
    target = os.path.join(TEXTS, f"{args.id:03d}.md")
    if args.text_file:
        text = open(args.text_file, encoding="utf-8").read().strip() + "\n"
        if not text.strip():
            sys.exit(f"{args.text_file} is empty")
    elif not os.path.exists(target):
        sys.exit(f"--text-file is required: {target} does not exist yet")

    cov = load_coverage()
    entry = {
        "id": args.id,
        "roman": "",
        "title": f"No. {args.id}",
        "start": {"book": sbook, "chapter": sch, "verse": sv},
        "end": {"book": ebook, "chapter": ech, "verse": ev},
    }
    homilies = [h for h in cov["homilies"] if h["id"] != args.id]
    replaced = len(homilies) != len(cov["homilies"])
    homilies.append(entry)
    homilies.sort(key=lambda h: h["id"])
    cov["homilies"] = homilies
    cov["total_homilies"] = len(homilies)

    summary = {
        "id": args.id,
        "text_file": os.path.relpath(target, os.getcwd()),
        "text_written": text is not None,
        "coverage_entry": "replaced" if replaced else "added",
        "range": f"{sbook} {sch}:{sv}" + ("" if (sch, sv) == (ech, ev) else f"-{ech}:{ev}"),
        "total_homilies": cov["total_homilies"],
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        print(json.dumps(summary, indent=2))
        return

    os.makedirs(TEXTS, exist_ok=True)
    if text is not None:
        open(target, "w", encoding="utf-8").write(text)
    with open(COVERAGE, "w", encoding="utf-8") as f:
        json.dump(cov, f, indent=4, ensure_ascii=False)
        f.write("\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Add Synaxarion citations to one or more verses.

Given verse(s), a calendar date, and a saint's name, write (or update) one entry in
texts/commentaries/synaxarion/coverage.json so those verses show a blue marker linking to
that saint's Life on the given day. Re-running with the same day+index+title merges new
verses into the existing entry (deduping).

Examples:
    add_citation.py --verse "matthew 18:2" --date 12-20 --saint "Ignatius of Antioch"
    add_citation.py --date 9/5 --saint "Zacharias" \\
        --title "Life of the Holy Prophet Zacharias" \\
        --verses "matthew 23:35, luke 1:5, luke 1:12, luke 3:2, luke 11:51"
"""

import argparse
import json
import re
import sys
from pathlib import Path

BOOK_SLUGS = {
    "matthew", "mark", "luke", "john", "acts", "romans", "1corinthians", "2corinthians",
    "galatians", "ephesians", "philippians", "colossians", "1thessalonians",
    "2thessalonians", "1timothy", "2timothy", "titus", "philemon", "hebrews", "james",
    "1peter", "2peter", "1john", "2john", "3john", "jude", "revelation",
}
BOOK_ALIASES = {"mt": "matthew", "mk": "mark", "lk": "luke", "jn": "john"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]


def find_repo_root(start: Path) -> Path:
    marker = Path("texts/commentaries/synaxarion/coverage.json")
    for base in [start, *start.parents]:
        if (base / marker).is_file():
            return base
    sys.exit("error: could not locate texts/commentaries/synaxarion/coverage.json")


def parse_verse(s: str):
    s = s.strip().replace(":", " ", 0)
    m = re.match(r"^(.*?)[\s]+(\d+)\s*[:.]\s*(\d+)$", s.strip())
    if not m:
        sys.exit(f"error: verse must look like 'matthew 18:2' (got '{s}')")
    book = m.group(1).strip().lower().replace(" ", "").rstrip(".")
    book = BOOK_ALIASES.get(book, book)
    if book not in BOOK_SLUGS:
        sys.exit(f"error: unknown book in verse '{s}': '{m.group(1).strip()}'")
    return {"book": book, "chapter": int(m.group(2)), "verse": int(m.group(3))}


def parse_verses(single, multi):
    raw = []
    if single:
        raw.append(single)
    if multi:
        raw.extend(p for p in re.split(r"[;,]", multi) if p.strip())
    if not raw:
        sys.exit("error: provide --verse or --verses")
    out = []
    for r in raw:
        v = parse_verse(r)
        if v not in out:
            out.append(v)
    return out


def parse_mmdd(s: str) -> str:
    s = s.strip()
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})$", s)
    if m:
        return f"{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = re.match(r"^([A-Za-z]+)\s+(\d{1,2})$", s)
    if m and m.group(1).lower() in MONTHS:
        return f"{MONTHS.index(m.group(1).lower()) + 1:02d}-{int(m.group(2)):02d}"
    sys.exit(f"error: --date must look like 12-20, 12/20, or 'December 20' (got '{s}')")


def month_folder(mmdd: str) -> str:
    m = int(mmdd[:2])
    return f"{m:02d}-{MONTHS[m - 1].capitalize()}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Add Synaxarion citation(s) to verse(s).")
    ap.add_argument("--verse", help="a single verse, e.g. 'matthew 18:2'")
    ap.add_argument("--verses", help="comma/semicolon list, e.g. 'lk 1:5, lk 1:12, mt 23:35'")
    ap.add_argument("--date", required=True, help="calendar day: 12-20, 12/20, or 'December 20'")
    ap.add_argument("--saint", required=True, help="saint name to match/display, e.g. 'Zacharias'")
    ap.add_argument("--title", help="marker title (default: 'Life of <saint>')")
    ap.add_argument("--index", type=int, help="commemoration index (default: match --saint that day)")
    ap.add_argument("--dry-run", action="store_true", help="print result, write nothing")
    args = ap.parse_args()

    verses = parse_verses(args.verse, args.verses)
    mmdd = parse_mmdd(args.date)
    title = args.title or f"Life of {args.saint}"

    root = find_repo_root(Path(__file__).resolve().parent)
    commem_path = root / "synaxarion" / "calendar" / month_folder(mmdd) / mmdd / "commemorations.json"
    if not commem_path.is_file():
        sys.exit(f"error: calendar day not found: {commem_path}\n"
                 f"       populate it with the orthodox-calendar skill first.")

    day = json.loads(commem_path.read_text(encoding="utf-8"))
    commems = day.get("commemorations", [])
    date_display = day.get("old_style_date", "")

    if args.index is not None:
        if not (0 <= args.index < len(commems)):
            sys.exit(f"error: --index {args.index} out of range ({len(commems)} on {mmdd})")
        index = args.index
    else:
        hits = [i for i, c in enumerate(commems) if args.saint.lower() in c.get("title", "").lower()]
        if not hits:
            listing = "\n".join(f"  {i}: {c['title']}" for i, c in enumerate(commems))
            sys.exit(f"error: no commemoration on {mmdd} matches '{args.saint}'. Choose --index:\n{listing}")
        if len(hits) > 1:
            listing = "\n".join(f"  {i}: {commems[i]['title']}" for i in hits)
            sys.exit(f"error: '{args.saint}' matches several on {mmdd}. Pick one with --index:\n{listing}")
        index = hits[0]

    saint_full = commems[index].get("title", args.saint)

    coverage_path = root / "texts/commentaries/synaxarion/coverage.json"
    data = json.loads(coverage_path.read_text(encoding="utf-8"))
    lives = data.setdefault("lives", [])

    entry = next((l for l in lives if l.get("mmdd") == mmdd
                  and l.get("commemoration_index") == index
                  and l.get("title") == title), None)
    added = 0
    if entry:
        for v in verses:
            if v not in entry["verses"]:
                entry["verses"].append(v)
                added += 1
        entry["saint"] = saint_full
        entry["date"] = date_display
        action = "updated"
    else:
        entry = {
            "id": max((l.get("id", 0) for l in lives), default=0) + 1,
            "title": title,
            "saint": saint_full,
            "date": date_display,
            "mmdd": mmdd,
            "commemoration_index": index,
            "verses": verses,
        }
        lives.append(entry)
        added = len(verses)
        action = "added"

    summary = {"action": action, "id": entry["id"], "title": title, "saint": saint_full,
               "date": date_display, "mmdd": mmdd, "commemoration_index": index,
               "verses_added": added, "verse_total": len(entry["verses"])}

    if args.dry_run:
        print(json.dumps({"dry_run": True, **summary}, indent=2, ensure_ascii=False))
        return

    coverage_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

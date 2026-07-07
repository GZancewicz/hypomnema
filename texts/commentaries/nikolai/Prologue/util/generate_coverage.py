import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KJV = os.path.join(BASE, "..", "..", "..", "scripture", "new_testament", "english", "kjv")

MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
CHURCH_YEAR = MONTHS[8:] + MONTHS[:8]

NT_BOOKS = {
    "matthew": "matthew", "mark": "mark", "luke": "luke", "john": "john",
    "acts": "acts", "acts of the apostles": "acts",
    "romans": "romans",
    "1 corinthians": "1corinthians", "2 corinthians": "2corinthians",
    "galatians": "galatians", "ephesians": "ephesians",
    "philippians": "philippians", "colossians": "colossians",
    "1 thessalonians": "1thessalonians", "2 thessalonians": "2thessalonians",
    "1 timothy": "1timothy", "2 timothy": "2timothy",
    "titus": "titus", "philemon": "philemon", "hebrews": "hebrews",
    "james": "james",
    "1 peter": "1peter", "2 peter": "2peter",
    "1 john": "1john", "2 john": "2john", "3 john": "3john",
    "jude": "jude", "revelation": "revelation",
}

CORRECTIONS = {
    ("march", 8): ("philippians", 2, 8, 8),
    ("march", 14): ("matthew", 26, 64, 64),
}

CITE_RE = re.compile(
    r"(?:St\.\s*)?"
    r"([123]?\s*[A-Z][a-z]+(?:\s+of\s+the\s+Apostles)?)"
    r"\s*(\d+)\s*[:.]\s*"
    r"(\d+(?:\s*[-,]\s*\d+)*)"
)

def normalize_book(name):
    name = name.strip().lower()
    name = re.sub(r"^([123])\s*", r"\1 ", name)
    return NT_BOOKS.get(name)

def parse_epigraph(epigraph):
    for m in CITE_RE.finditer(epigraph):
        book = normalize_book(m.group(1))
        if not book:
            continue
        chapter = int(m.group(2))
        verses = [int(v) for v in re.split(r"[-,]", m.group(3))]
        return book, chapter, verses[0], verses[-1]
    return None

def verse_exists(book, chapter, verse):
    path = os.path.join(KJV, book, f"{chapter:02d}", f"{book}_{chapter:02d}.txt")
    if not os.path.exists(path):
        return False
    text = open(path, encoding="utf-8").read()
    return re.search(rf"^({chapter}:)?{verse}\b", text, flags=re.M) is not None

def main():
    idx = json.load(open(os.path.join(BASE, "homilies.json"), encoding="utf-8"))
    by_date = {(e["month"], e["day"]): e for e in idx}

    homilies = []
    skipped = []
    invalid = []
    next_id = 1
    for month in CHURCH_YEAR:
        for day in range(1, 32):
            e = by_date.get((month, day))
            if not e:
                continue
            ref = CORRECTIONS.get((month, day)) or parse_epigraph(e["epigraph"])
            if not ref:
                skipped.append((e["date"], e["epigraph"]))
                continue
            book, chapter, v1, v2 = ref
            for v in (v1, v2):
                if not verse_exists(book, chapter, v):
                    invalid.append((e["date"], e["epigraph"], f"{book} {chapter}:{v}"))
            label = f"{month.capitalize()} {day}"
            homilies.append({
                "id": next_id,
                "roman": label,
                "title": label,
                "start": {"book": book, "chapter": chapter, "verse": v1},
                "end": {"book": book, "chapter": chapter, "verse": v2},
            })
            next_id += 1

    coverage = {
        "commentary": "Prologue of Ohrid",
        "total_homilies": len(homilies),
        "homilies": homilies,
    }
    out = os.path.join(BASE, "coverage.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(coverage, fh, indent=4, ensure_ascii=False)

    print(f"Wrote {len(homilies)} homilies to {out}")
    print(f"Skipped {len(skipped)} days without a NT citation")
    if invalid:
        print(f"INVALID references ({len(invalid)}):")
        for date, epi, ref in invalid:
            print(f"  {date}: {ref}  <-  {epi}")

if __name__ == "__main__":
    main()

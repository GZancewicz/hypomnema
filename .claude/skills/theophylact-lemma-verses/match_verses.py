#!/usr/bin/env python3
"""Deterministic Greek→Patriarchal verse matcher for Theophylact lemmata.

The atomic primitive of the theophylact-lemma-verses skill. NO LLM: pure stdlib
NLP. For each lemma in a chapter it matches the lemma's opening «…» Greek quote
against the verses of that same chapter in the Patriarchal (Byzantine) NT, using
TF-IDF cosine over normalized Greek tokens. Ranges are found by also matching the
quote's TAIL. A quote that matches nothing in its own chapter (a cross-reference or
a bare-exposition continuation) inherits the preceding lemma's verse by sequence —
never a foreign verse.

Usage:
    python3 match_verses.py --gospel matthew --chapter 1
    python3 match_verses.py --gospel matthew --chapter 1 --json   # machine-readable
    python3 match_verses.py --gospel matthew --chapter 1 --coverage-json > coverage_ch1.json

Output columns: lemma, folder-suffix, derived start–end, cosine score, quote head,
and a flag for every weak/cross-ref/continuation case to review.

Greek is the arbiter; the .en.md English is never read (its verse refs are unreliable).
"""
import argparse, json, math, re, sys, unicodedata, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]  # repo root from .claude/skills/<skill>/
GOSPEL_DIR = {"matthew": "ΚΑΤΑ_ΜΑΤΘΑΙΟΝ", "mark": "ΚΑΤΑ_ΜΑΡΚΟΝ",
              "luke": "ΚΑΤΑ_ΛΟΥΚΑΝ", "john": "ΚΑΤΑ_ΙΩΑΝΝΗΝ"}
SECTIONED = ROOT / "texts/commentaries/theophylact/PG/sectioned"
PATRIARCHAL = ROOT / "texts/scripture/new_testament/greek/patriarchal"
WEAK = 0.34  # cosine below this => treat as no in-chapter match (cross-ref/continuation)


def norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")  # drop accents/breathings
    s = s.lower().replace("ς", "σ")
    s = re.sub(r"[^α-ω ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def tokens(s):
    return [w for w in norm(s).split() if len(w) >= 3]


def load_chapter(gospel, chapter):
    f = PATRIARCHAL / gospel / f"{gospel}.txt"
    verses = {}
    for line in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^(\d+):(\d+)\s+(.*)$", line)
        if m and int(m.group(1)) == chapter:
            verses[int(m.group(2))] = tokens(m.group(3))
    if not verses:
        sys.exit(f"no {gospel} chapter {chapter} in Patriarchal text")
    return verses


def build_idf(verses):
    N = len(verses)
    df = {}
    for toks in verses.values():
        for w in set(toks):
            df[w] = df.get(w, 0) + 1
    return {w: math.log((N + 1) / (c + 0.5)) for w, c in df.items()}, N


def tfidf(toks, idf):
    v = {}
    for w in toks:
        v[w] = v.get(w, 0.0) + idf.get(w, math.log(2))  # unseen word: small weight
    return v


def cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(a[w] * b.get(w, 0.0) for w in a)
    na = math.sqrt(sum(x * x for x in a.values()))
    nb = math.sqrt(sum(x * x for x in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def best_verse(toks, verse_vecs, idf):
    q = tfidf(toks, idf)
    scored = sorted(((cosine(q, vv), v) for v, vv in verse_vecs.items()), reverse=True)
    return scored[0] if scored else (0.0, None)  # (score, verse)


def first_quote(txt):
    m = re.search(r"«(.*?)»", txt, re.S)
    if m:
        return m.group(1)
    m = re.search(r"(.*?)»", txt, re.S)  # OCR sometimes drops the opening «
    return m.group(1) if m else txt[:160]


def lemma_folders(gospel, chapter):
    erm = SECTIONED / GOSPEL_DIR[gospel] / "ΕΡΜΗΝΕΙΑ"
    hits = list(erm.glob(f"ΚΕΦΑΛΑΙΟΝ_{chapter:02d}_*/ΛΗΜΜΑ_*"))
    hits = [p for p in hits if p.is_dir()]
    return sorted(hits, key=lambda p: int(re.match(r"ΛΗΜΜΑ_(\d+)", p.name).group(1)))


def match_chapter(gospel, chapter, overrides=None):
    """overrides: {folder_name: [start, end]} adjudicated verses, applied BEFORE
    sequence-inheritance so downstream continuations inherit the corrected verse."""
    overrides = overrides or {}
    verses = load_chapter(gospel, chapter)
    idf, N = build_idf(verses)
    verse_vecs = {v: tfidf(t, idf) for v, t in verses.items()}
    vnums = sorted(verses)

    rows, prev = [], None
    for f in lemma_folders(gospel, chapter):
        idx = int(re.match(r"ΛΗΜΜΑ_(\d+)", f.name).group(1))
        suffix = re.match(r"ΛΗΜΜΑ_\d+_(\d+\.\d+)", f.name).group(1)
        quote = first_quote((f / f"{f.name}.txt").read_text(encoding="utf-8", errors="replace"))
        qtok = tokens(quote)

        if f.name in overrides:                     # adjudicated: trust it, set prev
            start, end = overrides[f.name]
            sc, conf, crossref = 1.0, "adjudicated", None
            prev = end
            rows.append(_row(idx, f.name, suffix, start, end, sc, conf, crossref, chapter, quote))
            continue

        sc, v = best_verse(qtok, verse_vecs, idf)
        # Single verse = the start match. Auto tail-ranging was removed: on this OCR
        # text it produced spurious wide ranges (a quote's tail collides with a
        # distant verse sharing a stock phrase, e.g. «βασιλεία τῶν οὐρανῶν»). Genuine
        # multi-verse spans are supplied via the overrides file instead.
        end = v

        crossref = None
        if v is None or sc < WEAK:
            # no in-chapter match -> cross-ref/continuation: inherit by sequence
            crossref = "weak/none in-chapter"
            start = end = prev
            conf = "low"
        else:
            start = v
            prev = end if end else v
            conf = "high" if sc >= 0.55 else "medium"

        rows.append(_row(idx, f.name, suffix, start, end, sc, conf, crossref, chapter, quote))
    return rows


def _row(idx, folder, suffix, start, end, sc, conf, crossref, chapter, quote):
    end = end if end else start
    sc_c, sc_v = suffix.split(".")
    agrees = None
    if start is not None:
        lo, hi = min(start, end), max(start, end)
        agrees = int(sc_c) == chapter and lo <= int(sc_v) <= hi
    return {
        "index": idx, "folder": folder, "suffix": suffix,
        "start": start, "end": end,
        "score": round(sc, 3), "conf": conf, "crossref": crossref,
        "folder_suffix_agrees": agrees,
        "quote_head": re.sub(r"\s+", " ", quote).strip()[:60],
    }


def chapters_of(gospel):
    erm = SECTIONED / GOSPEL_DIR[gospel] / "ΕΡΜΗΝΕΙΑ"
    return sorted(int(re.match(r"ΚΕΦΑΛΑΙΟΝ_(\d+)", p.name).group(1))
                  for p in erm.glob("ΚΕΦΑΛΑΙΟΝ_*") if p.is_dir())


def load_overrides(path):
    if not path:
        return {}
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def coverage_entries(g, chapter, rows):
    return [{
        "id": r["index"], "roman": "", "title": f"Lemma {r['index']}",
        "start": {"book": g, "chapter": chapter, "verse": r["start"]},
        "end": {"book": g, "chapter": chapter, "verse": r["end"]},
    } for r in rows if r["start"] is not None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gospel", required=True)
    ap.add_argument("--chapter", type=int, help="single chapter; omit with --all")
    ap.add_argument("--all", action="store_true", help="all chapters of the gospel")
    ap.add_argument("--overrides", help="JSON {folder_name:[start,end]} applied before inheritance")
    ap.add_argument("--json", action="store_true", help="raw match rows as JSON")
    ap.add_argument("--coverage-json", action="store_true", help="app coverage.json")
    ap.add_argument("--flags", action="store_true", help="only rows needing review")
    args = ap.parse_args()
    g = args.gospel.lower()
    ovr = load_overrides(args.overrides)
    chapters = chapters_of(g) if args.all else [args.chapter]
    if chapters == [None]:
        ap.error("give --chapter N or --all")

    per_ch = [(c, match_chapter(g, c, ovr)) for c in chapters]
    all_rows = [(c, r) for c, rows in per_ch for r in rows]

    if args.coverage_json:
        homilies = [h for c, rows in per_ch for h in coverage_entries(g, c, rows)]
        title = f"Explanation of the Holy Gospel According to {g.title()}"
        print(json.dumps({"commentary": f"Theophylact of Ohrid — {title}",
                          "note": "Section = Lemma N. Coverage: Greek«»→Patriarchal cosine (match_verses.py).",
                          "total_homilies": len(homilies), "homilies": homilies},
                         ensure_ascii=False, indent=2)); return
    if args.json:
        print(json.dumps([r for _, r in all_rows], ensure_ascii=False, indent=2)); return

    def flagged(r):
        return r["crossref"] is not None or r["folder_suffix_agrees"] is False \
            or r["start"] is None or r["start"] != r["end"]

    print(f"{g}: {len(chapters)} chapters, {len(all_rows)} lemmata"
          + (f", {sum(1 for _,r in all_rows if flagged(r))} flagged" if not args.flags else "") + "\n")
    print(f"{'lemma':16s} {'suf':6s} {'verse':>8s} {'cos':>5s}  quote / flag")
    for c, r in all_rows:
        if args.flags and not flagged(r):
            continue
        vr = "NONE" if r["start"] is None else (f"{r['start']}" if r["start"] == r["end"] else f"{r['start']}-{r['end']}")
        why = r["crossref"] or ("range" if r["start"] != r["end"] and r["start"] is not None else
                                ("suffix-off" if r["folder_suffix_agrees"] is False else ""))
        flag = f"  << {why}" if why else ""
        print(f"{r['folder']:16s} {r['suffix']:6s} {vr:>8s} {r['score']:5.2f}  {r['quote_head'][:44]}{flag}")


if __name__ == "__main__":
    main()

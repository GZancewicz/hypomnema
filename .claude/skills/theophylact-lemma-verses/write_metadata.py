#!/usr/bin/env python3
"""Write per-lemma metadata.json files from match_verses results.

Usage:
  python3 write_metadata.py --gospel matthew --chapter 1 --overrides overrides_matthew.json
  python3 write_metadata.py --gospel matthew --all --overrides overrides_matthew.json

For each lemma folder the derived coverage is written to
<lemma_folder>/metadata.json following the schema in SKILL.md.
Existing metadata.json files are overwritten only if --force is given or the
derived coverage differs; hand-curated fields (lemma_quote_en, cross_references,
notes) are preserved on rewrite unless --force.
"""
import argparse, json, re, sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import match_verses as mv

PRESERVE = ("lemma_quote_en", "cross_references", "notes")


def clean_quote(q):
    return re.sub(r"\s+", " ", q).strip()


def build_metadata(gospel, chapter, row, quote):
    cov_ch = row.get("chapter", chapter)
    start, end = row["start"], row["end"]
    lo, hi = (min(start, end), max(start, end)) if start is not None else (None, None)
    verses = [{"chapter": cov_ch, "verse": v} for v in range(lo, hi + 1)] if lo else []
    if lo is None:
        display = f"{gospel.capitalize()} {cov_ch}:?"
    elif lo == hi:
        display = f"{gospel.capitalize()} {cov_ch}:{lo}"
    else:
        display = f"{gospel.capitalize()} {cov_ch}:{lo}–{hi}"
    conf = row["conf"]
    if conf == "adjudicated":
        conf = "high"
    return {
        "lemma": row["folder"],
        "gospel": gospel,
        "chapter": chapter,
        "index": row["index"],
        "scripture_reference": {
            "book": gospel,
            "start": {"chapter": cov_ch, "verse": lo},
            "end": {"chapter": cov_ch, "verse": hi},
            "verses": verses,
            "display": display,
        },
        "lemma_quote": clean_quote(quote),
        "cross_references": [],
        "coverage_source": "greek_pat",
        "confidence": conf,
        "match_method": row.get("method"),
        "match_score": row["score"],
        "adjudicated": row["conf"] == "adjudicated",
        "continuation": row["crossref"] == "weak/none in-chapter",
        "folder_suffix": row["suffix"],
        "folder_suffix_agrees": row["folder_suffix_agrees"],
        "notes": "",
    }


def process_chapter(gospel, chapter, overrides, force=False):
    rows = mv.match_chapter(gospel, chapter, overrides)
    folders = {f.name: f for f in mv.lemma_folders(gospel, chapter)}
    written, skipped = 0, []
    for row in rows:
        folder = folders[row["folder"]]
        quote = mv.first_quote((folder / f"{folder.name}.txt").read_text(
            encoding="utf-8", errors="replace"))
        meta = build_metadata(gospel, chapter, row, quote)
        out = folder / "metadata.json"
        if out.exists() and not force:
            old = json.loads(out.read_text(encoding="utf-8"))
            for k in PRESERVE:
                if old.get(k):
                    meta[k] = old[k]
            if old.get("lemma_quote") and old.get("adjudicated", meta["adjudicated"]):
                meta["lemma_quote"] = old["lemma_quote"]
        if row["start"] is None:
            skipped.append(row["folder"])
            continue
        out.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        written += 1
        print(f"  {row['folder']:<20} -> {meta['scripture_reference']['display']}"
              f"  ({meta['confidence']}{', continuation' if meta['continuation'] else ''})")
    return written, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gospel", required=True, choices=list(mv.GOSPEL_DIR))
    ap.add_argument("--chapter", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--overrides")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    overrides = mv.load_overrides(args.overrides)
    chapters = mv.chapters_of(args.gospel) if args.all else [args.chapter]
    total, all_skipped = 0, []
    for ch in chapters:
        print(f"Chapter {ch}:")
        w, sk = process_chapter(args.gospel, ch, overrides, args.force)
        total += w
        all_skipped += sk
    print(f"\n{total} metadata.json written")
    if all_skipped:
        print(f"SKIPPED (no derivable verse — adjudicate in overrides): {all_skipped}")


if __name__ == "__main__":
    main()

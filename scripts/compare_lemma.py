#!/usr/bin/env python3
"""Bundle everything needed to compare ONE lemma's translation against the
Stade/Chrysostom Press benchmark: the Greek, our .en.md, and Stade's block for
that verse. Emits all three so the comparison skill can reason over them in one read.

Stade is in-copyright (benchmark/, git-ignored) — reference/QC only, never a source
of wording. The Greek is the arbiter; Stade is a second opinion.

Usage:
    python3 scripts/compare_lemma.py --gospel matthew --ch 5 --verse 3
    python3 scripts/compare_lemma.py --lemma texts/.../ΛΗΜΜΑ_06_5.3
    python3 scripts/compare_lemma.py --lemma <path-to>/ΛΗΜΜΑ_06_5.3/ΛΗΜΜΑ_06_5.3.txt

Only Matthew has a Stade benchmark downloaded so far; other gospels emit our
Greek + English and note that no Stade benchmark is present.
"""
import argparse, re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GOSPEL_DIR = {
    "matthew": "ΚΑΤΑ_ΜΑΤΘΑΙΟΝ",
    "mark": "ΚΑΤΑ_ΜΑΡΚΟΝ",
    "luke": "ΚΑΤΑ_ΛΟΥΚΑΝ",
    "john": "ΚΑΤΑ_ΙΩΑΝΝΗΝ",
}
SECTIONED = ROOT / "texts/commentaries/theophylact/PG/sectioned"


def stade_block(gospel, ch, verse):
    """Return (label, scripture, exposition) for the Stade block covering verse,
    or None if no benchmark / no block. Matthew only for now."""
    if gospel != "matthew":
        return None
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from align_stade_matthew import parse_stade, HTML
    except Exception as e:                       # pragma: no cover
        return None
    if not HTML.exists():
        return None
    blocks = parse_stade().get(ch, [])
    for a, b, sc, ex in blocks:
        if a <= verse <= b:
            label = f"{a}" if a == b else f"{a}-{b}"
            return (label, sc, ex)
    return None


def resolve_lemmas(args):
    """-> (gospel, [ (lemma_folder_path, ch, verse) ... ])"""
    if args.lemma:
        p = pathlib.Path(args.lemma)
        if p.is_file():
            p = p.parent
        p = p.resolve()
        m = re.match(r"ΛΗΜΜΑ_(\d+)_(\d+)\.(\d+)", p.name)
        if not m:
            sys.exit(f"not a lemma folder: {p}")
        # infer gospel from path
        gospel = next((g for g, d in GOSPEL_DIR.items() if d in p.parts), "matthew")
        return gospel, [(p, int(m.group(2)), int(m.group(3)))]

    gospel = args.gospel.lower()
    if gospel not in GOSPEL_DIR:
        sys.exit(f"unknown gospel: {gospel}")
    erm = SECTIONED / GOSPEL_DIR[gospel] / "ΕΡΜΗΝΕΙΑ"
    hits = []
    for folder in sorted(erm.glob(f"ΚΕΦΑΛΑΙΟΝ_{args.ch:02d}_*/ΛΗΜΜΑ_*_{args.ch}.{args.verse}")):
        m = re.match(r"ΛΗΜΜΑ_(\d+)_(\d+)\.(\d+)", folder.name)
        if m:
            hits.append((folder, args.ch, args.verse))
    if not hits:
        sys.exit(f"no lemma folder for {gospel} {args.ch}:{args.verse}")
    return gospel, hits


def read(folder, ext):
    f = folder / f"{folder.name}{ext}"
    return f.read_text(encoding="utf-8", errors="replace").strip() if f.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gospel")
    ap.add_argument("--ch", type=int)
    ap.add_argument("--verse", type=int)
    ap.add_argument("--lemma")
    args = ap.parse_args()
    if not args.lemma and not (args.gospel and args.ch and args.verse):
        ap.error("give either --lemma PATH or --gospel G --ch N --verse N")

    gospel, hits = resolve_lemmas(args)
    ch, verse = hits[0][1], hits[0][2]
    W = 78

    print("=" * W)
    print(f"COMPARE  {gospel.title()} {ch}:{verse}   ({len(hits)} lemma(s) on our side)")
    print("=" * W)

    for folder, ch, verse in hits:
        gr = read(folder, ".txt")
        en = read(folder, ".en.md")
        print(f"\n### LEMMA {folder.name}")
        print("\n--- GREEK (Theophylact, the arbiter) ---")
        print(gr if gr else "[missing]")
        print("\n--- OURS (.en.md) ---")
        print(en if en else "[NOT YET TRANSLATED]")

    st = stade_block(gospel, ch, verse)
    print("\n--- STADE (Chrysostom Press benchmark — reference only) ---")
    if st:
        label, sc, ex = st
        print(f"[Stade {gospel.title()} {ch}:{label}]")
        if sc:
            print(f"> {sc}")
        print(ex if ex else "[no exposition]")
    elif gospel != "matthew":
        print(f"[no Stade benchmark downloaded for {gospel} — Matthew only so far]")
    else:
        print("[no Stade block covers this verse "
              "(run scripts/align_stade_matthew.py; check benchmark/ is present)]")
    print("\n" + "=" * W)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build scripture-keyed commentary blocks for Theophylact.

The PG sectioning splits a single logical unit (scripture quote followed by
Theophylact's exposition) across several lemma folders: a long quote gets cut
at the column boundary, so one lemma holds only scripture and the exposition
lands in the next. Reading a lemma alone therefore shows a bare quote.

This groups consecutive lemmata into blocks that each end in exposition, and
keys them by the scripture they cover:

    {"book": "mt", "chapter": 21, "start_verse": 23, "end_verse": 24,
     "lemmata": [778, 779]}

Lemma ids are global (1..N per gospel), matching theophylactLemmaPaths() in
main.go: chapters sorted by name, then lemmata by their numeric prefix.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SECTIONED = ROOT / "texts/commentaries/theophylact/PG/sectioned"
OUT = ROOT / "texts/commentaries/theophylact"

GOSPEL_DIR = {
    "matthew": "ΚΑΤΑ_ΜΑΤΘΑΙΟΝ",
    "mark": "ΚΑΤΑ_ΜΑΡΚΟΝ",
    "luke": "ΚΑΤΑ_ΛΟΥΚΑΝ",
    "john": "ΚΑΤΑ_ΙΩΑΝΝΗΝ",
}
ABBREV = {"matthew": "mt", "mark": "mk", "luke": "lk", "john": "jn"}

EXPOSITION_MIN_CHARS = 40


def lemma_paths(gospel):
    erm = SECTIONED / GOSPEL_DIR[gospel] / "ΕΡΜΗΝΕΙΑ"
    chapters = sorted(
        (d for d in erm.iterdir() if d.is_dir() and d.name.startswith("ΚΕΦΑΛΑΙΟΝ")),
        key=lambda p: p.name,
    )
    paths = []
    for ch in chapters:
        lemmata = [d for d in ch.iterdir() if d.is_dir() and d.name.startswith("ΛΗΜΜΑ")]
        lemmata.sort(key=lambda p: int(p.name.split("_")[1]))
        paths.extend(lemmata)
    return paths


def normalized_text(path):
    return " ".join((path / (path.name + ".txt")).read_text(encoding="utf-8").split())


def has_exposition(text):
    """True when the lemma contributes commentary, not just scripture.

    A closing guillemet means the quote ended here, so anything substantial
    after it is exposition. Text that never opens a quote is already running
    prose. OCR drops guillemets often enough that neither test alone suffices.
    """
    if "»" in text:
        return len(text[text.rindex("»") + 1:].strip()) >= EXPOSITION_MIN_CHARS
    return not text.startswith("«")


def verse_ref(path):
    meta = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    return meta.get("scripture_reference") or {}


def build(gospel):
    paths = lemma_paths(gospel)

    blocks = []
    current = []
    for lemma_id, path in enumerate(paths, 1):
        current.append((lemma_id, path))
        if has_exposition(normalized_text(path)):
            blocks.append(current)
            current = []
    if current:
        # Trailing scripture with no exposition to close it; keep it rather
        # than dropping lemmata from the mapping.
        blocks.append(current)

    out = []
    for members in blocks:
        refs = [verse_ref(p) for _, p in members]
        starts = [(r["start"]["chapter"], r["start"]["verse"])
                  for r in refs if r.get("start")]
        ends = [(r["end"]["chapter"], r["end"]["verse"])
                for r in refs if r.get("end")]
        if not starts:
            continue

        # Anchor on the opening lemma and extend forward only. A block sometimes
        # begins with a stray fragment left over from the previous section, whose
        # low-confidence match points backwards; taking min()/max() would let that
        # outlier drag the range onto a passage the block never quotes.
        start_ch, start_v = starts[0]
        end_ch, end_v = start_ch, start_v
        for ch, v in ends:
            if (ch, v) > (end_ch, end_v):
                end_ch, end_v = ch, v

        entry = {
            "book": ABBREV[gospel],
            "chapter": start_ch,
            "start_verse": start_v,
            "end_verse": end_v,
            "lemmata": [i for i, _ in members],
        }
        if end_ch != start_ch:
            # Rare: a block whose quote runs past a chapter boundary.
            entry["end_chapter"] = end_ch
        out.append(entry)
    return out


def coverage_from_blocks(gospel, blocks):
    """One coverage entry per block, ids being the block's opening lemma.

    The reader addresses commentary by lemma id, so a block is named by the
    lemma that starts it; extractTheophylactGreek() expands that back to the
    whole block. Only these ids are surfaced as links.
    """
    entries = []
    for b in blocks:
        start_id = b["lemmata"][0]
        entries.append({
            "id": start_id,
            "roman": "",
            "title": f"Lemma {start_id}",
            "start": {"book": gospel, "chapter": b["chapter"], "verse": b["start_verse"]},
            "end": {"book": gospel,
                    "chapter": b.get("end_chapter", b["chapter"]),
                    "verse": b["end_verse"]},
        })
    return entries


def main():
    gospels = sys.argv[1:] or list(GOSPEL_DIR)
    for gospel in gospels:
        blocks = build(gospel)
        target = OUT / gospel
        target.mkdir(parents=True, exist_ok=True)

        path = target / "blocks.json"
        payload = {
            "commentary": f"Theophylact of Ohrid — Explanation of the Holy Gospel According to {gospel.title()}",
            "note": "Scripture-keyed blocks. Each block groups consecutive lemmata "
                    "ending in exposition; range spans its members "
                    "(build_theophylact_blocks.py).",
            "total_blocks": len(blocks),
            "blocks": blocks,
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

        coverage = coverage_from_blocks(gospel, blocks)
        cov_path = target / "coverage.json"
        cov_path.write_text(
            json.dumps({
                "commentary": f"Theophylact of Ohrid — Explanation of the Holy Gospel According to {gospel.title()}",
                "note": "Section = block, named by its opening lemma. Built from "
                        "blocks.json (build_theophylact_blocks.py).",
                "total_homilies": len(coverage),
                "homilies": coverage,
            }, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        covered = sum(len(b["lemmata"]) for b in blocks)
        print(f"{gospel:8s} {len(blocks):5d} blocks  {covered:5d} lemmata -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

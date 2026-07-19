#!/usr/bin/env python3
"""Per-verse comparison of our Theophylact translation vs the Stade benchmark.

Join key is the VERSE, sourced from the authoritative coverage (match_verses.py +
overrides) — NOT folder suffixes or .en.md refs. For each verse in a chapter it lists
our lemma .en.md(s) tagged to that verse against Stade's block covering that verse.
Many-of-ours -> one-of-Stade's is expected (e.g. Mt 1:1 -> Lemmata 1-5).

Output goes to benchmark/matthew/comparison_ch<NN>.md — inside the git-ignored
benchmark/ tree, because it embeds Stade's in-copyright text (reference/QC only).

Usage: python3 build_comparison.py --chapter 1
"""
import argparse, re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude/skills/theophylact-lemma-verses"))
sys.path.insert(0, str(ROOT / "scripts"))
import match_verses as mv                       # noqa: E402
from align_stade_matthew import parse_stade     # noqa: E402

OVERRIDES = ROOT / ".claude/skills/theophylact-lemma-verses/overrides_matthew.json"
OUT_DIR = ROOT / "texts/commentaries/theophylact/benchmark/matthew"


def en_md_body(folder):
    f = folder / f"{folder.name}.en.md"
    if not f.exists():
        return "_(not yet translated)_"
    lines = [ln for ln in f.read_text(encoding="utf-8").splitlines()
             if not re.match(r"\s*\[\^\d+\]:", ln)]          # drop footnote defs
    body = re.sub(r"\[\^\d+\]", "", "\n".join(lines))        # drop footnote refs
    body = re.sub(r"(?m)^#.*$", "", body)                    # drop H1
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ch = ap.parse_args().chapter

    import json
    ovr = json.loads(OVERRIDES.read_text(encoding="utf-8"))
    rows = mv.match_chapter("matthew", ch, ovr)               # authoritative verse per lemma
    base = mv.SECTIONED / mv.GOSPEL_DIR["matthew"] / "ΕΡΜΗΝΕΙΑ"
    folders = {p.name: p for p in mv.lemma_folders("matthew", ch)}

    ours = {}                                                 # verse -> [(idx, folder)]
    for r in rows:
        if r["start"] is not None:
            ours.setdefault(r["start"], []).append((r["index"], folders[r["folder"]]))

    stade = {}                                                # verse -> (label, sc, ex)
    for a, b, sc, ex in parse_stade().get(ch, []):
        label = f"{a}" if a == b else f"{a}-{b}"
        for v in range(a, b + 1):
            stade[v] = (label, sc, ex)

    out = [f"# Matthew {ch} — ours vs. Stade (per verse, keyed on coverage.json)",
           "", "_Git-ignored: embeds Stade (in-copyright), QC reference only._", ""]
    for v in sorted(set(ours) | set(stade)):
        out.append(f"## {ch}:{v}\n")
        out.append("### Ours")
        if v in ours:
            for idx, folder in sorted(ours[v]):
                out.append(f"**Lemma {idx}** (`{folder.name}`)\n")
                out.append(en_md_body(folder) + "\n")
        else:
            out.append("_(no lemma of ours tagged to this verse)_\n")
        out.append("### Stade")
        if v in stade:
            label, sc, ex = stade[v]
            out.append(f"**Stade {ch}:{label}**\n")
            if sc:
                out.append(f"> {sc}\n")
            out.append((ex or "_(no exposition)_") + "\n")
        else:
            out.append("_(no Stade block for this verse)_\n")
        out.append("---\n")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dst = OUT_DIR / f"comparison_ch{ch:02d}.md"
    dst.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {dst}  ({len(ours)} verses with our lemmata, {len(stade)} Stade verses)")


if __name__ == "__main__":
    main()

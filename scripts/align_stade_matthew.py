#!/usr/bin/env python3
"""Align the Stade/Chrysostom Press Matthew translation (benchmark, git-ignored)
against our own per-lemma .en.md translations, keyed on chapter.verse.

Stade side: parsed from benchmark/matthew/stade_matthew.html. Scripture lemmata are
in <B> runs; each is preceded by a bold verse number ("3.", "4. Blessed are..."),
and body chapters are marked by <A ...>Chapter Word.</A> anchors.

Our side: PG/sectioned/.../ΚΑΤΑ_ΜΑΤΘΑΙΟΝ/ΕΡΜΗΝΕΙΑ/ΚΕΦΑΛΑΙΟΝ_*/ΛΗΜΜΑ_NN_ch.verse/*.en.md

Output: benchmark/matthew/alignment/ch_NN.md — one file per chapter, each verse a
side-by-side block (ours vs Stade), plus alignment/INDEX.md coverage summary.
Everything under benchmark/ is git-ignored.
"""
import re, html, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BENCH = ROOT / "texts/commentaries/theophylact/benchmark/matthew"
HTML = BENCH / "stade_matthew.html"
OURS_DIR = (ROOT / "texts/commentaries/theophylact/PG/sectioned"
            / "ΚΑΤΑ_ΜΑΤΘΑΙΟΝ/ΕΡΜΗΝΕΙΑ")
OUT = BENCH / "alignment"

WORDS = ("One Two Three Four Five Six Seven Eight Nine Ten Eleven Twelve Thirteen "
         "Fourteen Fifteen Sixteen Seventeen Eighteen Nineteen Twenty Twenty-One "
         "Twenty-Two Twenty-Three Twenty-Four Twenty-Five Twenty-Six Twenty-Seven "
         "Twenty-Eight").split()
WORD2NUM = {w.lower(): i + 1 for i, w in enumerate(WORDS)}


def clean(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = html.unescape(s)
    s = s.replace("\xa0", " ").replace("’", "'").replace("�", "'")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def parse_stade():
    """-> {chapter:int -> [ (verse:int, scripture:str, exposition:str) ]}"""
    raw = HTML.read_text(encoding="utf-8", errors="replace")
    # Body chapter anchors look like  ...>Chapter Five</A>.  (TOC ones have </B></A>).
    # Find body start = the LAST-group set of chapter anchors (second occurrence onward).
    anchors = [(m.start(), m.group(1))
               for m in re.finditer(r">Chapter ([A-Za-z-]+)\s*\.?\s*</A>", raw)]
    # Keep only body anchors: those after the front-matter/TOC. The TOC set is the
    # first run of monotonically-listed chapters; body set restarts at "One".
    ones = [i for i, (_, w) in enumerate(anchors) if w.lower() == "one"]
    body_start_idx = ones[-1] if ones else 0
    body_anchors = anchors[body_start_idx:]
    if not body_anchors:
        sys.exit("no body chapter anchors found")

    # slice raw into chapter segments
    segs = []
    for k, (pos, word) in enumerate(body_anchors):
        num = WORD2NUM.get(word.lower())
        if not num:
            continue
        end = body_anchors[k + 1][0] if k + 1 < len(body_anchors) else len(raw)
        segs.append((num, raw[pos:end]))

    chapters = {}
    for num, seg in segs:
        # mark bold, drop other tags
        seg = re.sub(r"(?i)<b\b[^>]*>", "\x01", seg)
        seg = re.sub(r"(?i)</b>", "\x02", seg)
        seg = re.sub(r"<[^>]+>", " ", seg)
        seg = html.unescape(seg).replace("\xa0", " ")
        seg = seg.replace("’", "'").replace("�", "'")

        # Walk, tracking bold depth, into a list of (is_bold, text) tokens
        toks, depth, buf = [], 0, []

        def flush(b):
            t = "".join(buf)
            if t.strip():
                toks.append((b, t))
            buf.clear()
        i = 0
        while i < len(seg):
            c = seg[i]
            if c == "\x01":
                flush(depth > 0); depth += 1
            elif c == "\x02":
                flush(depth > 0); depth = max(0, depth - 1)
            else:
                buf.append(c)
            i += 1
        flush(depth > 0)

        # Merge into verse blocks. A new block starts at a BOLD token beginning
        # with a verse number or range: "3.", "1-2.", "23-24."
        verses = []
        cur = None
        vnum_re = re.compile(r"^\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?\.\s*(.*)$", re.S)
        for is_bold, text in toks:
            m = vnum_re.match(text) if is_bold else None
            if m:
                if cur:
                    verses.append(cur)
                a = int(m.group(1))
                b = int(m.group(2)) if m.group(2) else a
                cur = {"a": a, "b": max(a, b),
                       "scripture": [], "exposition": []}
                rest = m.group(3).strip()
                if rest:
                    cur["scripture"].append(rest)
            elif cur is not None:
                (cur["scripture"] if is_bold else cur["exposition"]).append(text)
        if cur:
            verses.append(cur)

        out = []
        for v in verses:
            sc = re.sub(r"\s+", " ", " ".join(v["scripture"])).strip()
            ex = re.sub(r"\s+", " ", " ".join(v["exposition"])).strip()
            if sc or ex:
                out.append((v["a"], v["b"], sc, ex))
        if out:
            chapters[num] = out
    return chapters


def parse_ours():
    """-> {(chapter,verse) -> [ {folder, lemma_scripture, body, file} ]}"""
    data = {}
    for md in sorted(OURS_DIR.glob("ΚΕΦΑΛΑΙΟΝ_*/ΛΗΜΜΑ_*/*.en.md")):
        folder = md.parent.name          # ΛΗΜΜΑ_NN_ch.verse
        m = re.match(r"ΛΗΜΜΑ_(\d+)_(\d+)\.(\d+)", folder)
        if not m:
            continue
        idx, ch, vs = int(m.group(1)), int(m.group(2)), int(m.group(3))
        txt = md.read_text(encoding="utf-8", errors="replace")
        # strip footnote definitions (lines starting [^n]:)
        body_lines = [ln for ln in txt.splitlines()
                      if not re.match(r"\s*\[\^\d+\]:", ln)]
        body = "\n".join(body_lines)
        # lemma scripture = first blockquote bold  > **...**
        qm = re.search(r">\s*\*\*(.+?)\*\*", body, re.S)
        lemma = re.sub(r"\s+", " ", qm.group(1)).strip() if qm else ""
        # exposition = text after the blockquote, minus the H1 heading
        prose = re.sub(r"(?m)^#.*$", "", body)
        prose = re.sub(r"(?m)^>.*$", "", prose)
        prose = re.sub(r"\[\^\d+\]", "", prose)          # drop footnote refs
        prose = re.sub(r"\n{2,}", "\n\n", prose).strip()
        data.setdefault((ch, vs), []).append(
            {"idx": idx, "folder": folder, "lemma": lemma,
             "prose": prose, "file": str(md.relative_to(ROOT))})
    for k in data:
        data[k].sort(key=lambda d: d["idx"])
    return data


def main():
    stade = parse_stade()
    ours = parse_ours()
    OUT.mkdir(exist_ok=True)

    our_chapters = sorted({ch for ch, _ in ours})
    index = ["# Matthew — ours vs. Stade (Chrysostom Press) benchmark",
             "",
             "Git-ignored. Stade text is in-copyright — reference/QC only.",
             "",
             "| Ch | verses (ours) | verses (Stade) | both | ours-only | Stade-only |",
             "|----|----|----|----|----|----|"]

    for ch in our_chapters:
        our_v = {v for (c, v) in ours if c == ch}
        blocks = stade.get(ch, [])                       # [(a,b,sc,ex)]
        # map each covered verse -> block, and a label for the block's range
        st = {}
        st_v = set()
        for a, b, sc, ex in blocks:
            label = f"{a}" if a == b else f"{a}-{b}"
            for v in range(a, b + 1):
                st[v] = (label, sc, ex)
                st_v.add(v)
        both = sorted(our_v & st_v)
        oo = sorted(our_v - st_v)
        so = sorted(st_v - our_v)
        index.append(f"| {ch} | {len(our_v)} | {len(st_v)} | {len(both)} "
                     f"| {len(oo)} | {len(so)} |")

        lines = [f"# Matthew {ch} — ours vs. Stade", ""]
        shown = None                                     # dedupe repeated range block
        for v in sorted(our_v | st_v):
            lines.append(f"## {ch}:{v}")
            lines.append("")
            lines.append("### Ours")
            if (ch, v) in ours:
                for d in ours[(ch, v)]:
                    lines.append(f"**[{d['folder']}]** > {d['lemma']}")
                    lines.append("")
                    lines.append(d["prose"] if d["prose"] else "_(no prose)_")
                    lines.append("")
            else:
                lines.append("_(no lemma on our side for this verse)_")
                lines.append("")
            lines.append("### Stade")
            if v in st:
                label, sc, ex = st[v]
                if label == shown:
                    lines.append(f"_(continues Stade block {label}, shown above)_")
                else:
                    shown = label
                    lines.append(f"**Stade {ch}:{label}**")
                    lines.append("")
                    if sc:
                        lines.append(f"> {sc}")
                        lines.append("")
                    lines.append(ex if ex else "_(no exposition)_")
            else:
                lines.append("_(no verse block in Stade)_")
            lines.append("")
            lines.append("---")
            lines.append("")
        (OUT / f"ch_{ch:02d}.md").write_text("\n".join(lines), encoding="utf-8")

    (OUT / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print("Stade chapters parsed:", sorted(stade))
    print("Our chapters:", our_chapters)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()

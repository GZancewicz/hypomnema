#!/usr/bin/env python3
"""Apply confirmed verse ranges to Cyril-on-Luke coverage, metadata, and verse map.

Usage:
  python apply_coverage.py <commentary_dir> <results.json>

<results.json> is a list of
  {"id": int, "start": {"chapter": int, "verse": int},
   "end": {"chapter": int, "verse": int}}
produced by the reading pass (extra keys like evidence/confidence are ignored).

Unlike the Chrysostom apply script, START is also rewritten here (the source
metadata contains 1:1 placeholders). Additionally:
  - roman/title in coverage.json are recomputed from the sermon id (fixes
    copied-from-neighbor labels)
  - content/<NNN>/metadata.json scripture_reference and subtitle are updated
  - verse_mapping.json (chapter -> sermon list) is regenerated from coverage
Prints a validation report (bounds vs KJV Luke, overlaps, gaps).
"""
import sys, os, json, re, glob

def i2r(n):
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out

def flat(c, v): return c * 1000 + v

def disp(s, e):
    if s["chapter"] == e["chapter"]:
        if s["verse"] == e["verse"]:
            return f"Luke {s['chapter']}:{s['verse']}"
        return f"Luke {s['chapter']}:{s['verse']}-{e['verse']}"
    return f"Luke {s['chapter']}:{s['verse']}-{e['chapter']}:{e['verse']}"

def load_verse_counts(cdir):
    root = cdir
    for _ in range(6):
        cand = glob.glob(os.path.join(root, "scripture", "**", "kjv", "luke", "*", "*.txt"), recursive=True)
        if cand: break
        root = os.path.dirname(root)
    else:
        return {}
    counts = {}
    for f in cand:
        m = re.search(r'_(\d+)\.txt$', f)
        if not m: continue
        ch = int(m.group(1)); mx = 0
        for line in open(f, encoding='utf-8'):
            mm = re.match(r'(\d+):(\d+)\s', line)
            if mm and int(mm.group(1)) == ch:
                mx = max(mx, int(mm.group(2)))
        counts[ch] = mx
    return counts

def main():
    cdir = sys.argv[1]
    res = json.load(open(sys.argv[2]))
    ranges = {r["id"]: r for r in res}
    covp = os.path.join(cdir, "coverage.json")
    cov = json.load(open(covp))
    vcount = load_verse_counts(cdir)

    homs = sorted(cov["homilies"], key=lambda h: h["id"])
    errs, gaps, overlaps = [], [], []

    for h in homs:
        sid = h["id"]
        h["roman"] = i2r(sid)
        h["title"] = f"Sermon {i2r(sid)}"
        if sid not in ranges:
            errs.append(f"S{sid}: no result provided")
            continue
        r = ranges[sid]
        s, e = r["start"], r["end"]
        if flat(e["chapter"], e["verse"]) < flat(s["chapter"], s["verse"]):
            errs.append(f"S{sid}: end {e} before start {s}")
            continue
        for cv, name in ((s, "start"), (e, "end")):
            if vcount:
                if cv["chapter"] not in vcount:
                    errs.append(f"S{sid}: {name} chapter {cv['chapter']} not in Luke")
                elif cv["verse"] > vcount[cv["chapter"]]:
                    errs.append(f"S{sid}: {name} {cv['chapter']}:{cv['verse']} exceeds last verse {vcount[cv['chapter']]}")
        h["start"], h["end"] = s, e

        mp = os.path.join(cdir, "content", f"{sid:03d}", "metadata.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            m["scripture_reference"] = {
                "book": "luke", "start": s, "end": e, "display": disp(s, e),
            }
            m["subtitle"] = disp(s, e)
            json.dump(m, open(mp, "w"), ensure_ascii=False, indent=2)

    for i, h in enumerate(homs[:-1]):
        n = homs[i + 1]
        he, ns = h.get("end"), n.get("start")
        if not he or not ns: continue
        ef, nf = flat(he["chapter"], he["verse"]), flat(ns["chapter"], ns["verse"])
        same_start = flat(h["start"]["chapter"], h["start"]["verse"]) == nf
        if ef >= nf and not same_start:
            overlaps.append(f"S{h['id']} ends {he['chapter']}:{he['verse']} >= S{n['id']} starts {ns['chapter']}:{ns['verse']}")
        elif ef < nf - 1:
            gaps.append(f"after S{h['id']} ({he['chapter']}:{he['verse']}) until S{n['id']} ({ns['chapter']}:{ns['verse']})")

    cov["total_homilies"] = len(homs)
    cov["homilies"] = homs
    json.dump(cov, open(covp, "w"), ensure_ascii=False, indent=2)

    vm = {}
    for h in homs:
        if "start" not in h: continue
        for ch in range(h["start"]["chapter"], h["end"]["chapter"] + 1):
            vm.setdefault(str(ch), [])
            if not any(x["id"] == h["id"] for x in vm[str(ch)]):
                vm[str(ch)].append({"id": h["id"], "roman": h["roman"]})
    for ch in vm:
        vm[ch].sort(key=lambda x: x["id"])
    json.dump(vm, open(os.path.join(cdir, "verse_mapping.json"), "w"), ensure_ascii=False, indent=2)

    print(f"applied {len(ranges)} ranges; coverage.json, metadata, verse_mapping.json updated")
    print(f"validation errors ({len(errs)}): {errs if errs else 'NONE'}")
    print(f"overlaps not explained by shared start ({len(overlaps)}) — expected for 'continued' chains:")
    for o in overlaps: print("  " + o)
    print(f"gaps ({len(gaps)}) — real where sermons are lost:")
    for g in gaps: print("  " + g)

if __name__ == "__main__":
    main()

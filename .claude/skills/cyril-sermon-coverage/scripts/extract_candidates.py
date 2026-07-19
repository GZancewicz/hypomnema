#!/usr/bin/env python3
"""Extract per-sermon coverage candidates for Cyril of Alexandria on Luke.

Unlike the CCEL ThML pipeline (Chrysostom), the source here is Payne Smith
HTML already parsed into content/<NNN>/content.json. Verse citations appear
inline in the prose as paragraph-leading lemmata ("12:22-31.", "(6:24)",
"Luke ii. 1") rather than as scripRef tags. Both START and END of each
sermon's range are treated as unknown: the existing metadata contains 1:1
placeholders, mislabeled romans, and single-verse lemma ranges.

For each sermon this yields:
  - candidate_start: first paragraph-leading citation near the top (lemma)
  - candidate_end: furthest citation within the window
      [candidate_start (or prev sermon start for continuations), next extant
       sermon's candidate_start)
  - continued: True when the sermon is titled "the same subject continued"
  - lead/inline citation lists, previous/next extant sermon context
  - plain text written to <text_dir>/<NNN>.txt for the reading pass

Usage:
  python extract_candidates.py <commentary_dir> <out_manifest.json> [<text_dir>]
"""
import sys, os, re, json, glob, html

def i2r(n):
    vals = [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),
            (50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]
    out = ''
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out

ROM = {'I':1,'V':5,'X':10,'L':50,'C':100}
def r2i(s):
    s = s.strip().upper(); t = 0; p = 0
    for ch in reversed(s):
        if ch not in ROM: return None
        v = ROM[ch]; t += -v if v < p else v; p = max(p, v)
    return t

MAX_CH = 24  # Luke

LEAD = re.compile(
    r'^\(?\s*(\d{1,2})\s*:\s*(\d{1,3})'
    r'(?:\s*[-–]\s*(?:(\d{1,2})\s*:\s*)?(\d{1,3}))?\s*\)?\s*[.,;]?\s')
LUKE_NAMED = re.compile(
    r'\bLuke\s+(?:([ivxlc]+)\.|(\d{1,2})\s*:)\s*(\d{1,3})'
    r'(?:\s*[-–]\s*(?:(\d{1,2})\s*:\s*)?(\d{1,3}))?', re.I)
INLINE = re.compile(
    r'(?<=[.?!"”]\s)\(?(\d{1,2})\s*:\s*(\d{1,3})'
    r'(?:\s*[-–]\s*(?:(\d{1,2})\s*:\s*)?(\d{1,3}))?\)?[.,;]\s')
CONTINUED = re.compile(r'same\s+subject\s+continued|upon\s+the\s+same\s+subject', re.I)

def flat(c, v): return c * 1000 + v

def strip_para(p):
    t = re.sub(r'<sup>.*?</sup>', '', p)
    t = html.unescape(re.sub(r'<[^>]+>', '', t))
    return re.sub(r'\s+', ' ', t).strip()

def norm_ref(g_ch, g_v, g_ech, g_ev):
    sc, sv = int(g_ch), int(g_v)
    if sc < 1 or sc > MAX_CH or sv < 1 or sv > 200:
        return None
    if g_ev:
        ec = int(g_ech) if g_ech else sc
        ev = int(g_ev)
        if ec < sc or ec > MAX_CH or ev < 1 or ev > 200:
            ec, ev = sc, sv
        if flat(ec, ev) < flat(sc, sv):
            ec, ev = sc, sv
    else:
        ec, ev = sc, sv
    return {"start": {"chapter": sc, "verse": sv}, "end": {"chapter": ec, "verse": ev}}

def para_citations(paras):
    lead, inline = [], []
    for i, p in enumerate(paras):
        t = strip_para(p)
        if not t: continue
        m = LEAD.match(t)
        if m:
            r = norm_ref(m.group(1), m.group(2), m.group(3), m.group(4))
            if r: lead.append({"para": i, **r})
        for m in LUKE_NAMED.finditer(t):
            if m.group(1) is not None:
                ch = r2i(m.group(1))
                if not ch: continue
                r = norm_ref(ch, m.group(3), None, m.group(5))
            else:
                r = norm_ref(m.group(2), m.group(3), m.group(4), m.group(5))
            if r: lead.append({"para": i, **r})
        for m in INLINE.finditer(t):
            r = norm_ref(m.group(1), m.group(2), m.group(3), m.group(4))
            if r: inline.append({"para": i, **r})
    return lead, inline

def main():
    cdir = sys.argv[1]; out = sys.argv[2]
    text_dir = sys.argv[3] if len(sys.argv) > 3 else None
    if text_dir: os.makedirs(text_dir, exist_ok=True)

    cov = json.load(open(os.path.join(cdir, "coverage.json")))
    cov_by_id = {h["id"]: h for h in cov["homilies"]}
    ids = sorted(cov_by_id)

    sermons = {}
    for sid in ids:
        p = os.path.join(cdir, "content", f"{sid:03d}", "content.json")
        c = json.load(open(p))
        paras = c.get("paragraphs", [])
        lead, inline = para_citations(paras)
        head = " ".join(strip_para(x) for x in paras[:2])[:300]
        continued = bool(CONTINUED.search(head))
        cand_start = None
        for r in lead:
            if r["para"] <= 2:
                cand_start = r["start"]; break
        sermons[sid] = {
            "paras": paras, "lead": lead, "inline": inline,
            "continued": continued, "cand_start": cand_start, "head": head,
        }
        if text_dir:
            txt = "\n\n".join(t for t in (strip_para(x) for x in paras) if t)
            open(os.path.join(text_dir, f"{sid:03d}.txt"), "w").write(txt)

    manifest = []
    prev_start = None
    for idx, sid in enumerate(ids):
        s = sermons[sid]
        cur = cov_by_id[sid]
        nxt_id = ids[idx + 1] if idx + 1 < len(ids) else None
        nxt_start = None
        if nxt_id is not None:
            nxt_start = sermons[nxt_id]["cand_start"] or cov_by_id[nxt_id]["start"]
        win_start = s["cand_start"] or (prev_start if s["continued"] else None)
        cand_end = None
        if win_start:
            lo = flat(win_start["chapter"], win_start["verse"])
            hi = flat(nxt_start["chapter"], nxt_start["verse"]) if nxt_start else 10**9
            best = None
            for r in s["lead"] + s["inline"]:
                for cv in (r["start"], r["end"]):
                    f = flat(cv["chapter"], cv["verse"])
                    if lo <= f < max(hi, lo + 1) and (best is None or f > flat(best["chapter"], best["verse"])):
                        best = cv
            cand_end = best
        placeholder = cur["start"] == {"chapter": 1, "verse": 1} and cur["end"] == {"chapter": 1, "verse": 1} and sid not in (0,)
        manifest.append({
            "id": sid,
            "roman": i2r(sid),
            "label_in_coverage": cur["roman"],
            "label_mismatch": cur["roman"] != i2r(sid),
            "current": {"start": cur["start"], "end": cur["end"]},
            "placeholder_1_1": placeholder and sid != 1,
            "continued": s["continued"],
            "candidate_start": s["cand_start"],
            "candidate_end": cand_end,
            "prev_extant": ({"id": ids[idx-1], "start": prev_start} if idx > 0 else None),
            "next_extant": ({"id": nxt_id, "start": nxt_start} if nxt_id else None),
            "lead_citations": s["lead"],
            "inline_citations": s["inline"],
            "opening_text": s["head"],
            "text_file": (os.path.join(text_dir, f"{sid:03d}.txt") if text_dir else None),
        })
        prev_start = s["cand_start"] or (prev_start if s["continued"] else cur["start"])

    json.dump(manifest, open(out, "w"), ensure_ascii=False, indent=2)
    n_ph = sum(1 for e in manifest if e["current"]["start"] == {"chapter": 1, "verse": 1} and e["id"] != 1 and e["current"]["end"] == {"chapter": 1, "verse": 1})
    n_lab = sum(1 for e in manifest if e["label_mismatch"])
    n_cont = sum(1 for e in manifest if e["continued"])
    n_nostart = sum(1 for e in manifest if not e["candidate_start"])
    print(f"sermons={len(manifest)} manifest={out}")
    print(f"1:1 placeholders={n_ph}  label mismatches={n_lab}  'continued' sermons={n_cont}  no lemma detected={n_nostart}")

if __name__ == "__main__":
    main()

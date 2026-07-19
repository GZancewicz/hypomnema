#!/usr/bin/env python3
"""Apply confirmed last-verse-covered ends to a commentary's coverage + metadata.

Usage:
  python apply_coverage.py <commentary_dir> <results.json>

<results.json> is a list of {"id": int, "end": {"chapter": int, "verse": int}}
produced by the reading pass. Updates coverage.json (each homily's END) and each
content/<NNN>/metadata.json 'coverage' block, recomputing display strings.
START verses (the lemma) are never changed. Prints a validation report.
"""
import sys, os, json, re, glob

def load_verse_counts(cdir, book):
    """Best-effort: last verse number per chapter, from the repo's KJV text."""
    # texts/commentaries/<author>/<book> -> texts/scripture/.../kjv/<book>
    root=cdir
    for _ in range(6):
        cand=glob.glob(os.path.join(root,"scripture","**","kjv",book,"*","*.txt"), recursive=True)
        if cand: break
        root=os.path.dirname(root)
    else:
        return {}
    counts={}
    for f in cand:
        m=re.search(r'_(\d+)\.txt$', f)
        if not m: continue
        ch=int(m.group(1)); mx=0
        for line in open(f, encoding='utf-8'):
            mm=re.match(r'(\d+):(\d+)\s', line)
            if mm and int(mm.group(1))==ch: mx=max(mx, int(mm.group(2)))
        counts[ch]=mx
    return counts

def flat(c,v): return c*1000+v
def disp(book, s, e):
    b=book.capitalize()
    if s["chapter"]==e["chapter"]:
        if s["verse"]==e["verse"]: return f"{b} {s['chapter']}:{s['verse']}"
        return f"{b} {s['chapter']}:{s['verse']}-{e['verse']}"
    return f"{b} {s['chapter']}:{s['verse']}-{e['chapter']}:{e['verse']}"

def main():
    cdir=sys.argv[1]; res=json.load(open(sys.argv[2]))
    ends={r["id"]: r["end"] for r in res}
    cov=json.load(open(os.path.join(cdir,"coverage.json")))
    book=cov["commentary"].split("_",1)[1] if "_" in cov["commentary"] else cov["commentary"]

    vcount=load_verse_counts(cdir, book)
    def next_verse(c,v):
        if vcount and c in vcount and v>=vcount[c]: return (c+1,1)
        return (c,v+1)

    homs=sorted(cov["homilies"], key=lambda h:h["id"])
    errs=[]; gaps=[]
    for i,h in enumerate(homs):
        if h["id"] not in ends:
            errs.append(f"H{h['id']}: no result provided"); continue
        e=ends[h["id"]]; s=h["start"]
        if flat(e["chapter"],e["verse"]) < flat(s["chapter"],s["verse"]):
            errs.append(f"H{h['id']}: end {e} before start {s}"); continue
        h["end"]=e
        # overlap check vs next homily's start
        if i+1<len(homs):
            ns=homs[i+1]["start"]
            if flat(e["chapter"],e["verse"]) >= flat(ns["chapter"],ns["verse"]):
                # allowed only when they share a start (multiple homilies on same verse)
                if flat(ns["chapter"],ns["verse"])!=flat(s["chapter"],s["verse"]):
                    errs.append(f"H{h['id']}: end {e} overlaps next start {ns}")
            else:
                nc,nv=next_verse(e["chapter"],e["verse"])  # first verse after this end
                if flat(nc,nv) < flat(ns["chapter"],ns["verse"]):  # a genuine uncovered verse exists
                    gaps.append((h["id"], (nc,nv), ns))
        # update metadata coverage block
        mp=os.path.join(cdir,"content",f"{h['id']:03d}","metadata.json")
        if os.path.exists(mp):
            m=json.load(open(mp))
            m["coverage"]={"start":s,"end":e,"display":disp(book,s,e)}
            json.dump(m, open(mp,"w"), ensure_ascii=False, indent=2)

    json.dump(cov, open(os.path.join(cdir,"coverage.json"),"w"), ensure_ascii=False, indent=2)
    print(f"applied {len(ends)} ends to {book}; coverage.json + metadata updated")
    print(f"validation errors: {errs if errs else 'NONE'}")
    def prev_verse(c,v):
        if v>1: return (c,v-1)
        return (c-1, vcount.get(c-1, v-1))
    print(f"real gaps ({len(gaps)}) - verses no homily covers:")
    for hid,(gc,gv),ns in gaps:
        lc,lv=prev_verse(ns["chapter"],ns["verse"])  # last uncovered verse
        rng=f"{gc}:{gv}" if (gc,gv)==(lc,lv) else f"{gc}:{gv}-{lc}:{lv}"
        print(f"  after H{hid}: {rng} uncovered (next homily opens at {ns['chapter']}:{ns['verse']})")

if __name__=="__main__":
    main()

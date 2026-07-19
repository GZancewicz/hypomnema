#!/usr/bin/env python3
"""Build one analysis bundle per homily: the FULL commentary text + the actual
KJV verses of the passage, so an LLM can read the commentary against the biblical
text and judge where the exposition ends. This is plumbing only — it makes NO
determination about coverage; the LLM does that (see SKILL.md).

Usage:
  python build_bundles.py <commentary_dir> <out_dir>

Writes <out_dir>/bundles/<NNN>.txt and <out_dir>/manifest.json.
Book and start lemmata are read from <commentary_dir>/coverage.json; the KJV text
is located automatically under .../texts/scripture/**/kjv/<book>/.
"""
import sys, os, re, json, glob

def load_kjv(book_dir):
    kjv={}
    for f in glob.glob(os.path.join(book_dir,"*","*.txt")):
        m=re.search(r'_(\d+)\.txt$', f)
        if not m: continue
        ch=int(m.group(1)); d={}
        for line in open(f, encoding='utf-8'):
            mm=re.match(r'(\d+):(\d+)\s+(.*)', line.strip())
            if mm and int(mm.group(1))==ch: d[int(mm.group(2))]=mm.group(3)
        kjv[ch]=d
    return kjv

def find_kjv_dir(cdir, book):
    root=cdir
    for _ in range(7):
        hits=glob.glob(os.path.join(root,"scripture","**","kjv",book), recursive=True)
        if hits: return hits[0]
        root=os.path.dirname(root)
    return None

def commentary_text(cdir, cid):
    p=os.path.join(cdir,"content",f"{cid:03d}","content.json")
    if not os.path.exists(p): return ""
    c=json.load(open(p)); out=[]
    for para in c.get("paragraphs",[]):
        t=re.sub(r'<sup>.*?</sup>','',para)
        t=re.sub(r'<[^>]+>','',t).strip()
        if t: out.append(t)
    return "\n\n".join(out)

def main():
    cdir=sys.argv[1]; outdir=sys.argv[2]
    cov=json.load(open(os.path.join(cdir,"coverage.json")))
    book=cov["commentary"].split("_",1)[1] if "_" in cov["commentary"] else cov["commentary"]
    Book=book.capitalize()
    kjv_dir=find_kjv_dir(cdir, book)
    if not kjv_dir: sys.exit(f"could not locate KJV text for '{book}'")
    kjv=load_kjv(kjv_dir); maxv={c:max(v) for c,v in kjv.items() if v}
    unit=cov.get("unit","Homily")

    homs=sorted(cov["homilies"], key=lambda h:h["id"])
    os.makedirs(os.path.join(outdir,"bundles"), exist_ok=True)
    manifest=[]
    for i,h in enumerate(homs):
        hid=h["id"]; s=h["start"]
        nxt=homs[i+1]["start"] if i+1<len(homs) else {"chapter":max(kjv), "verse":maxv[max(kjv)]+1}
        end_ch=min(max(nxt["chapter"], s["chapter"]), s["chapter"]+3, max(kjv))
        bible=[f"{ch}:{v} {kjv[ch][v]}" for ch in range(s["chapter"], end_ch+1)
               for v in sorted(kjv.get(ch,{}))]
        bundle=(f"{unit.upper()} {h['roman']} (id {hid})\n"
                f"Opening lemma (authoritative START of coverage): {Book} {s['chapter']}:{s['verse']}\n"
                f"The NEXT {unit.lower()} opens at {Book} {nxt['chapter']}:{nxt['verse']} "
                f"(informational upper bound; coverage ends at or before there, may stop earlier).\n\n"
                f"===== COMMENTARY TEXT ({unit} {h['roman']}) =====\n{commentary_text(cdir,hid)}\n\n"
                f"===== KJV {Book} {s['chapter']}:{s['verse']}-{end_ch}:{maxv[end_ch]} "
                f"(compare the commentary against these verses) =====\n" + "\n".join(bible) + "\n")
        path=os.path.join(outdir,"bundles",f"{hid:03d}.txt")
        open(path,"w",encoding='utf-8').write(bundle)
        manifest.append({"id":hid,"roman":h["roman"],"start":s,"next_start":nxt,"bundle":path})
    json.dump(manifest, open(os.path.join(outdir,"manifest.json"),"w"), ensure_ascii=False, indent=2)
    print(f"built {len(manifest)} bundles for {book} -> {outdir}/bundles/")

if __name__=="__main__":
    main()

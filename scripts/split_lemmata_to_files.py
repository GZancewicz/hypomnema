import sys, os, re, json, unicodedata, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import sect_dir

WORD=re.compile(r'[Α-Ωα-ωΆ-ῼἀ-῾]+')
def strip(s):
    s=unicodedata.normalize('NFD',s); s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^α-ω]','',s.lower().replace('ς','σ'))
def wm(a,b): return a==b or (len(a)>=5 and len(b)>=5 and a[:5]==b[:5] and abs(len(a)-len(b))<=1)
GOSPEL={'ΚΑΤΑ_ΜΑΤΘΑΙΟΝ':'matthew','ΚΑΤΑ_ΜΑΡΚΟΝ':'mark','ΚΑΤΑ_ΛΟΥΚΑΝ':'luke','ΚΑΤΑ_ΙΩΑΝΝΗΝ':'john'}
def load_tr(gospel,ch):
    out={}
    for l in open(f'texts/scripture/new_testament/greek/textus_receptus/{gospel}/{gospel}.txt',encoding='utf-8'):
        m=re.match(rf'^{ch}:(\d+)\s+(.*)',l)
        if m: out[int(m.group(1))]=[strip(w) for w in WORD.findall(m.group(2)) if len(strip(w))>=5]
    return out
def subseq(op, win):
    p=0;m=0
    for w in op:
        while p<len(win) and not wm(w,win[p]): p+=1
        if p<len(win): m+=1;p+=1
    return m
def tag_verse(words8, tr, floor, wide=False):
    rng=sorted(tr) if wide else range(floor, floor+6)
    best=(None,0)
    for v in rng:
        if v not in tr: continue
        sc=subseq(tr[v][:5], words8)
        if sc>best[1]: best=(v,sc)
    thr=3 if wide else 2
    return best[0] if best[1]>=thr else None

def process(path, gfolder, entry, apply):
    gospel=GOSPEL[gfolder]; ch=entry['chapter']
    full=open(path,encoding='utf-8').read()
    lines=full.split('\n'); header=lines[0]; body='\n'.join(lines[1:])
    toks=[(strip(m.group(0)), m.start()) for m in WORD.finditer(body) if strip(m.group(0))]
    tr=load_tr(gospel,ch)
    guills=[m.start() for m in re.finditer('«',body)]
    bounds=set(guills)                 # every « is a lemma boundary (his own division)
    wi=0                               # gap-fill: verses whose « was OCR-dropped
    for v in sorted(tr):
        op=tr[v][:4]
        if not op: continue
        for i in range(wi,len(toks)):
            if not wm(op[0],toks[i][0]): continue
            if subseq(op[1:], [t[0] for t in toks[i:i+10]])>=min(2,len(op)-1):
                c=toks[i][1]
                if not any(-70<=c-g<=10 for g in guills): bounds.add(c)
                wi=i+1; break
    merged=[]
    for b in sorted(bounds):
        if merged and b-merged[-1]<25: continue   # drop OCR-noise «/near-dupes
        merged.append(b)
    if not merged: return None
    files=[('00_ΑΡΧΗ.txt', header+'\n'+body[:merged[0]])]
    segs=[(b, merged[k+1] if k+1<len(merged) else len(body)) for k,b in enumerate(merged)]
    verses=[]; cursor=1; established=False
    for b,e in segs:
        w8=[strip(w) for w in WORD.findall(body[b:e][:120])][:8]
        v=tag_verse(w8, tr, cursor, wide=not established)
        if v is not None: cursor=v; established=True
        verses.append(v)
    lastv=None                                # inherit for unmatched fragments (forward)
    for i in range(len(verses)):
        if verses[i] is None: verses[i]=lastv
        else: lastv=verses[i]
    nxt=None                                   # backward fill for leading fragments
    for i in range(len(verses)-1,-1,-1):
        if verses[i] is None: verses[i]=nxt
        else: nxt=verses[i]
    for k,(b,e) in enumerate(segs):
        vlabel=f'{ch}.{verses[k]}' if verses[k] else f'{ch}.?'
        files.append((f'ΛΗΜΜΑ_{k+1:02d}_{vlabel}.txt', body[b:e]))
    assert ''.join(t for _,t in files)==full, f"INTEGRITY FAIL {path}"
    if apply:
        folder=os.path.splitext(path)[0]; os.makedirs(folder,exist_ok=True)
        # intro file at chapter-folder level
        open(os.path.join(folder,'00_ΑΡΧΗ.txt'),'w',encoding='utf-8').write(files[0][1])
        # one SUBFOLDER per lemma, holding the Greek (translation .en.md added later)
        for name,txt in files[1:]:
            stem=os.path.splitext(name)[0]
            ldir=os.path.join(folder,stem); os.makedirs(ldir,exist_ok=True)
            open(os.path.join(ldir,name),'w',encoding='utf-8').write(txt)
        # keep the full chapter .txt, moved inside its folder
        shutil.move(path, os.path.join(folder, os.path.basename(path)))
    return files

def main():
    apply='--apply' in sys.argv
    only=[a for a in sys.argv[1:] if not a.startswith('--')]
    base=sect_dir(); idx=json.load(open(os.path.join(base,'lemmata_index.json'),encoding='utf-8'))
    nch=nl=0
    for rel,entry in idx.items():
        if only and not any(o in rel for o in only): continue
        gf=rel.split('/')[0]; path=os.path.join(base,rel)
        if not os.path.exists(path): continue
        r=process(path,gf,entry,apply)
        if r is None: continue
        nch+=1; nl+=len(r)-1
        if only:
            print(f"{rel}: {len(r)-1} lemma files + intro")
            for name,txt in r[:10]:
                print(f"    {name:20} {txt.strip().splitlines()[0][:44] if txt.strip() else ''}")
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {nch} chapters, {nl} lemma files"+("" if apply else "  — --apply"))
if __name__=='__main__': main()

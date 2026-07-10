import re, unicodedata, json, glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import sect_dir, numeral_from_name

WORD=re.compile(r'[Α-Ωα-ωΆ-ῼἀ-῾]+')
def strip(s):
    s=unicodedata.normalize('NFD',s)
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^α-ω]','',s.lower().replace('ς','σ'))

def tokenize(text):
    toks=[]
    for m in WORD.finditer(text):
        nw=strip(m.group(0))
        if nw: toks.append((nw, m.start()))
    return toks

GOSPEL={'ΚΑΤΑ_ΜΑΤΘΑΙΟΝ':'matthew','ΚΑΤΑ_ΜΑΡΚΟΝ':'mark','ΚΑΤΑ_ΛΟΥΚΑΝ':'luke','ΚΑΤΑ_ΙΩΑΝΝΗΝ':'john'}
def load_tr(gospel, chapter):
    path=f'texts/scripture/new_testament/greek/textus_receptus/{gospel}/{gospel}.txt'
    out={}
    for l in open(path,encoding='utf-8'):
        m=re.match(rf'^{chapter}:(\d+)\s+(.*)',l)
        if m:
            vw=[strip(w) for w in WORD.findall(m.group(2))]
            out[int(m.group(1))]=[w for w in vw if len(w)>=3]
    return out

def wmatch(a,b): return a==b or (len(a)>=4 and len(b)>=4 and a[:4]==b[:4])

def find_verse(Wn, distinct, start):
    if not distinct: return None
    L=max(len(distinct)+2,4); nd=len(distinct)
    for i in range(start, len(Wn)-1):
        win=Wn[i:i+L]
        s=sum(1 for vw in distinct if any(wmatch(vw,x) for x in win))
        if s/nd>=0.6:
            # local refine to max
            bi,bf=i,s/nd
            for j in range(i,min(i+5,len(Wn))):
                w2=Wn[j:j+L]; s2=sum(1 for vw in distinct if any(wmatch(vw,x) for x in w2))
                if s2/nd>bf: bi,bf=j,s2/nd
            return (bi,bf)
    return None

def segment(path, gfolder):
    gospel=GOSPEL[gfolder]
    chapter=int(re.search(r'ΚΕΦΑΛΑΙΟΝ_(\d+)_',os.path.basename(path)).group(1))
    text='\n'.join(open(path,encoding='utf-8').read().split('\n')[1:])  # drop header
    toks=tokenize(text); Wn=[t[0] for t in toks]
    tr=load_tr(gospel,chapter)
    lemmata=[]; pos=0
    for v in sorted(tr):
        r=find_verse(Wn,tr[v],pos)
        if r:
            i,frac=r; pos=i+1
            preview=text[toks[i][1]: toks[i][1]+60].replace('\n',' ')
            lemmata.append({'verse':f'{chapter}:{v}','char':toks[i][1],
                            'score':round(frac,2),'preview':preview})
    covered=[int(l['verse'].split(':')[1]) for l in lemmata]
    return {'gospel':gospel,'chapter':chapter,'tr_verses':len(tr),
            'verses_covered':len(covered),
            'range':f'{chapter}:{min(covered)}-{chapter}:{max(covered)}' if covered else None,
            'lemma_count':len(lemmata),'lemmata':lemmata}

def main():
    base=sect_dir(); out={}
    for gf in GOSPEL:
        for path in sorted(glob.glob(os.path.join(base,gf,'ΕΡΜΗΝΕΙΑ','ΚΕΦΑΛΑΙΟΝ_*.txt'))):
            rel=os.path.relpath(path,base)
            out[rel]=segment(path,gf)
    json.dump(out,open(os.path.join(base,'lemmata_index.json'),'w',encoding='utf-8'),
              ensure_ascii=False,indent=1)
    # summary
    tot_l=sum(v['lemma_count'] for v in out.values())
    print(f"segmented {len(out)} chapters, {tot_l} lemmata -> sectioned/lemmata_index.json\n")
    print(f"{'chapter':<40}{'cov/tr':>8}{'lemmata':>9}  range")
    low=[]
    for rel,v in out.items():
        cov=f"{v['verses_covered']}/{v['tr_verses']}"
        pct=v['verses_covered']/v['tr_verses'] if v['tr_verses'] else 0
        flag='  <-- LOW' if pct<0.5 else ''
        if pct<0.5: low.append(rel)
        name='/'.join(rel.split('/')[::2]) if False else rel.split('/')[0][5:]+'/'+os.path.basename(rel)
        print(f"{name:<40}{cov:>8}{v['lemma_count']:>9}  {v['range']}{flag}")
    print(f"\nchapters with <50% verse coverage (check): {len(low)}")
if __name__=='__main__': main()

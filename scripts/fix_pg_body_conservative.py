import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import sect_dir
GREEK=re.compile(r'[Ͱ-Ͽἀ-῿]+')
PERI={'Ιερὶ','Τερὶ','Ζερὶ','ΙΙερὶ','ερὶ','κερὶ','ἰερὶ','λερὶ','τερὶ','ἱερὶ','ἵερὶ','Ιερί','ἱερί','ἰερί'}
EXACT={'Ἰλσοῦ':'Ἰησοῦ','Ἐησοῦ':'Ἰησοῦ','Ἰησους':'Ἰησοῦς','Ἰησου':'Ἰησοῦ',
       'Χριστου':'Χριστοῦ','Χριστού':'Χριστοῦ','Χριστοὺ':'Χριστοῦ'}
SENT=set('.·;»:)')
def fix_line(line):
    out=[]; last=0; changes=[]
    for m in GREEK.finditer(line):
        tok=m.group(0); rep=None
        if tok in EXACT: rep=EXACT[tok]
        elif tok in PERI:
            pre=line[:m.start()].rstrip()
            cap = (pre=='' or (pre and pre[-1] in SENT))
            rep='Περὶ' if cap else 'περὶ'
        if rep and rep!=tok:
            out.append(line[last:m.start()]); out.append(rep); last=m.end()
            changes.append((tok,rep))
    out.append(line[last:])
    return ''.join(out), changes
def main():
    apply='--apply' in sys.argv
    base=sect_dir(); tot=0; from collections import Counter; c=Counter()
    for f in glob.glob(os.path.join(base,'*','ΕΡΜΗΝΕΙΑ','ΚΕΦΑΛΑΙΟΝ_*.txt')):
        lines=open(f,encoding='utf-8').read().split('\n')
        new=[]; fchg=0
        for idx,l in enumerate(lines):
            if idx==0: new.append(l); continue   # keep header line untouched
            nl,ch=fix_line(l); new.append(nl)
            for a,b in ch: c[(a,b)]+=1; fchg+=1
        tot+=fchg
        if apply and fchg: open(f,'w',encoding='utf-8').write('\n'.join(new))
    for (a,b),n in c.most_common(): print(f"  {n:4}  {a} -> {b}")
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {tot} token replacements")
if __name__=='__main__': main()

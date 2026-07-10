import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import *
def main():
    base=sect_dir()
    lc=orp=rh=0
    for f in all_txt(base):
        for l in open(f,encoding='utf-8'):
            s=l.strip()
            if not s: continue
            if latin_caput(s): lc+=1
            elif orphan_numeral(s): orp+=1
            elif runhead_noise(s,f): rh+=1
    # header issues
    hd=0
    for f in chapter_files(base):
        first=open(f,encoding='utf-8').readline().strip()
        want=f"ΚΕΦΑΛ. {numeral_from_name(f)}"
        if first.replace('.','').replace(' ','')!=want.replace('.','').replace(' ',''): hd+=1
    print(f"header-issues={hd}  latin-caput={lc}  orphan-numerals={orp}  runhead-noise={rh}")
if __name__=='__main__': main()

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import *
def main():
    apply='--apply' in sys.argv
    base=sect_dir(); removed=0; files_ch=0
    for f in all_txt(base):
        lines=open(f,encoding='utf-8').read().split('\n')
        keep=[]; rem=[]
        for ln in lines:
            s=ln.strip()
            if s and is_noise(s,f): rem.append(s)
            else: keep.append(ln)
        if rem:
            files_ch+=1; removed+=len(rem)
            rel=os.path.relpath(f,base)
            for r in rem: print(f"  - {rel}: '{r}'")
            if apply:
                open(f,'w',encoding='utf-8').write('\n'.join(keep))
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {removed} lines in {files_ch} files"
          +("" if apply else "  (re-run with --apply to write)"))
if __name__=='__main__': main()

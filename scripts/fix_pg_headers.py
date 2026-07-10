import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pg_common import *
def main():
    apply='--apply' in sys.argv
    base=sect_dir(); med=medconf_set(base); n=0
    for f in chapter_files(base):
        num=numeral_from_name(f); want=f"ΚΕΦΑΛ. {num}."
        lines=open(f,encoding='utf-8').read().split('\n')
        first=lines[0].strip()
        if first==want:
            continue
        rel=os.path.relpath(f,base)
        if f in med:
            action=f"PREPEND '{want}'  (keep titlos: '{first[:30]}')"
            new=[want]+lines
        else:
            action=f"REPLACE '{first[:30]}' -> '{want}'"
            new=[want]+lines[1:]
        n+=1; print(f"  {rel}: {action}")
        if apply: open(f,'w',encoding='utf-8').write('\n'.join(new))
    print(f"\n{'APPLIED' if apply else 'DRY-RUN'}: {n} headers"
          +("" if apply else "  (re-run with --apply to write)"))
if __name__=='__main__': main()

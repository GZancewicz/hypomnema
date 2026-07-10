import re, os, glob, json

def sect_dir():
    here=os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here,'..','texts','commentaries','theophylact','PG','sectioned')

def chapter_files(base):
    return sorted(glob.glob(os.path.join(base,'*','ΕΡΜΗΝΕΙΑ','ΚΕΦΑΛΑΙΟΝ_*.txt')))
def all_txt(base):
    return sorted(glob.glob(os.path.join(base,'*','ΕΡΜΗΝΕΙΑ','*.txt'))+glob.glob(os.path.join(base,'*','*.txt')))

def latin_caput(s):
    toks=s.split()
    if len(toks)!=2 or not(3<=len(s)<=16): return False
    a,b=toks; b=b.strip('.,·')
    if 'ΚΕΦ' in a.upper(): return False
    if not re.match(r'^[Α-Ωα-ωϹβζ]{3,6}$',a) or a[0] not in 'ΟΛΔΕΑΘϹβζΚ': return False
    return bool(re.match(r'^[ΧΚΙΝνvΥΤιlIi]{1,6}$',b))

def orphan_numeral(s):
    t=s.strip('.,·;')
    return bool(1<=len(t)<=6 and 'ʹ' not in s and re.match(r'^[ΧΙνviΚ]+$',t)
               and re.search(r'[Χvi]',t.lower()) and t not in ('Ι','ΙΙ'))

_RUN=[re.compile(p) for p in [r'ΘΕΟΦΥΛ',r'Θεοφυλ',r'ΒΟΥΛΓΑΡ',r'ΑΡΧΙΕΠ',r'ΛΡΧΙΕΠ',r'ΤΟΥ ΑΓΙΟΥ']]
def runhead_noise(s, path):
    return bool('ΚΕΦΑΛΑΙΟΝ_' in path and len(s)<45 and any(p.search(s) for p in _RUN))

def is_noise(s, path):
    return latin_caput(s) or orphan_numeral(s) or runhead_noise(s,path)

def numeral_from_name(path):
    m=re.search(r'ΚΕΦΑΛΑΙΟΝ_\d+_(.+)\.txt$', os.path.basename(path))
    return m.group(1) if m else None

def medconf_set(base):
    m=json.load(open(os.path.join(base,'MANIFEST.json'),encoding='utf-8'))
    short={'ΚΑΤΑ_ΜΑΤΘΑΙΟΝ':'ΜΑΤΘΑΙΟΝ','ΚΑΤΑ_ΜΑΡΚΟΝ':'ΜΑΡΚΟΝ','ΚΑΤΑ_ΛΟΥΚΑΝ':'ΛΟΥΚΑΝ','ΚΑΤΑ_ΙΩΑΝΝΗΝ':'ΙΩΑΝΝΗΝ'}
    out=set()
    for g,d in m['gospels'].items():
        for c in d['chapters']:
            if c['confidence']=='medium':
                out.add(os.path.join(base,g,c['file']))
    return out

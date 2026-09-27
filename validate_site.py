from pathlib import Path
from bs4 import BeautifulSoup
import re,json,sys
ROOT=Path(__file__).resolve().parent
fail=0
rows=[]
for p in sorted(ROOT.rglob('*.html')):
    s=BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser')
    c=BeautifulSoup(str(s),'html.parser')
    for t in c(['script','style','noscript','template']): t.decompose()
    for sel in ['[data-xenors-build]','.xenors-skip-link','nav']:
        for x in c.select(sel): x.decompose()
    words=len(re.findall(r"\b[\w’'-]+\b",' '.join(c.stripped_strings)))
    title=bool(s.title and s.title.get_text(strip=True))
    desc=bool(s.find('meta',attrs={'name':'description','content':True}))
    canon=bool(s.find('link',rel='canonical',href=True))
    ld=s.find_all('script',attrs={'type':'application/ld+json'})
    ld_ok=bool(ld)
    for x in ld:
        try: json.loads(x.string or x.get_text())
        except Exception: ld_ok=False
    head=title and desc and canon and ld_ok and bool(s.find('meta',attrs={'property':'og:title'})) and bool(s.find('meta',attrs={'name':'twitter:card'}))
    hdr=len(s.select('[data-xenors-build="header"]'))==1
    ftr=len(s.select('[data-xenors-build="footer"]'))==1
    path='/' + str(p.relative_to(ROOT)).replace('\\','/')
    need_ra=not any(x in path for x in ['/login/','/signup/','/privacy-policy/','/terms/','/404.html'])
    ra=(len(s.select('[data-xenors-build="read-also"]'))==1) if need_ra else True
    ok=words>=1000 and head and hdr and ftr and ra
    rows.append((ok,words,path,head,hdr,ftr,ra,len(ld)))
    if not ok: fail+=1
print('STATUS WORDS PAGE HEAD HEADER FOOTER READ_ALSO JSONLD')
for r in rows: print(('PASS' if r[0] else 'FAIL'),r[1],r[2],*r[3:])
print(f'\nTOTAL={len(rows)} PASS={len(rows)-fail} FAIL={fail}')
sys.exit(1 if fail else 0)

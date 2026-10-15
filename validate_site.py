from pathlib import Path
from bs4 import BeautifulSoup
import re,json,sys
ROOT=Path(__file__).resolve().parent
errors=[]; warnings=[]
htmls=[p for p in ROOT.rglob('*.html') if 'dist' not in p.parts]
canon=[]
for p in htmls:
    rel=str(p.relative_to(ROOT)).replace('\\','/')
    if 'components/' in rel or '/_shared/' in rel: continue
    s=BeautifulSoup(p.read_text(errors='ignore'),'html.parser')
    c=s.find('link',rel='canonical'); r=s.find('meta',attrs={'name':'robots'})
    if c and 'noindex' not in ((r.get('content','') if r else '').lower()):
        u=c.get('href',''); canon.append(u)
        if u.endswith('.html'): errors.append(rel+': .html canonical')
    if 'FAQPage' in p.read_text(errors='ignore'): errors.append(rel+': FAQPage schema')
    if rel=='web-stories/index.html' and len(s.find_all('h1'))>1: errors.append(rel+': multiple H1')
sm=(ROOT/'sitemap.xml').read_text(errors='ignore')
locs=re.findall(r'<loc>(.*?)</loc>',sm)
if len(locs)!=len(set(locs)): errors.append('duplicate sitemap URLs')
for u in set(canon):
    if u.startswith('https://xenors.in/') and '404' not in u and u not in locs: errors.append('canonical missing from sitemap: '+u)
if (ROOT/'favicon.ico').exists() and (ROOT/'favicon.ico').stat().st_size>50000: warnings.append('favicon.ico >50KB')
large=[p for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'} and p.stat().st_size>500000]
if large: warnings.append(str(len(large))+' images >500KB')
D=ROOT/'dist'
if D.exists():
    bad=[p for p in D.rglob('*') if p.is_file() and (p.suffix.lower() in {'.py','.csv','.md','.zip','.yaml','.yml'} or p.name in {'build.py','render.yaml'})]
    if bad: errors.append('public source files in dist')
print(json.dumps({'html_pages':len(htmls),'unique_canonicals':len(set(canon)),'sitemap_urls':len(locs),'errors':errors,'warnings':warnings},indent=2))
if errors: sys.exit(1)

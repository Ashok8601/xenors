from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json,csv,re,sys
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
pages=json.loads((ROOT/'config/pages.json').read_text(encoding='utf-8'))
utils=json.loads((ROOT/'config/utility_pages.json').read_text(encoding='utf-8'))
all_pages=pages+utils
canonical_paths={urlparse(p['url']).path for p in pages}
served_paths={urlparse(p['url']).path for p in all_pages}
errors=[]
for p in all_pages:
    path=urlparse(p['url']).path
    f=DIST/'index.html' if path=='/' else DIST/path.strip('/')/'index.html'
    if not f.exists(): errors.append(f'MISSING PAGE: {path} -> {f}') ; continue
    soup=BeautifulSoup(f.read_text(encoding='utf-8',errors='ignore'),'html.parser')
    c=soup.find('link',rel=lambda v:v and 'canonical' in (v if isinstance(v,list) else [v]))
    if not c or c.get('href')!=p['url']: errors.append(f'BAD CANONICAL: {path}')
    if not soup.title or not soup.title.get_text(strip=True): errors.append(f'MISSING TITLE: {path}')
    if not soup.find('meta',attrs={'name':re.compile('^description$',re.I)}): errors.append(f'MISSING DESCRIPTION: {path}')
    if p in utils:
        r=soup.find('meta',attrs={'name':re.compile('^robots$',re.I)})
        if not r or 'noindex' not in r.get('content','').lower(): errors.append(f'UTILITY MUST BE NOINDEX: {path}')
with (ROOT/'config/redirects.csv').open(encoding='utf-8') as fh:
    for r in csv.DictReader(fh):
        dst=r['new_url']
        if ':splat' in dst: continue
        if dst=='/sitemap.xml': continue
        if dst not in served_paths:
            errors.append(f'REDIRECT TARGET NOT SERVED: {r["old_url"]} -> {dst}')
if errors:
    print('\n'.join(errors)); sys.exit(1)
print(f'OK: {len(pages)} indexable pages + {len(utils)} utility pages; redirect targets valid.')

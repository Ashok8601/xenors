from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from PIL import Image
import argparse,csv,json,re,sys,xml.etree.ElementTree as ET

ap=argparse.ArgumentParser(); ap.add_argument('--root',default='dist'); args=ap.parse_args(); ROOT=Path(args.root).resolve(); SITE='https://xenors.in'
errors=[]; warnings=[]
NOINDEX={'/404.html','/login/','/signup/'}
UTILITY={'/','/404.html','/login/','/signup/','/search/','/contact/','/about/','/careers/','/mission/','/privacy-policy/','/cookie-policy/','/terms/','/editorial-policy/','/how-we-test/','/sitemap/','/ai/','/tech/','/coding/','/plc/','/finance/','/share-market/','/blog/','/crypto/','/stock-market/','/business-news/','/machine-learning/','/machine-learning-projects/','/data-science/','/interview-preparation/','/ai/tools/','/ai/models/','/ai/news/','/finance/investing/','/finance/trading/','/finance/stocks/','/coding/flask/','/coding/django/','/coding/python-data/'}
UTILITY_PREFIX=('/web-stories/','/home/code-lab/')
APPROVED={'www.googletagmanager.com','cdn.onesignal.com'}

def url_for(p):
    rel=p.relative_to(ROOT).as_posix()
    if rel=='index.html':return '/'
    if rel=='404.html':return '/404.html'
    if rel.endswith('/index.html'):return '/'+rel[:-10]
    return None

def target_exists(path,redirects):
    if path=='/': return (ROOT/'index.html').exists()
    if path=='/404.html': return (ROOT/'404.html').exists()
    p=ROOT/path.lstrip('/')
    if p.is_file(): return True
    if (p/'index.html').exists(): return True
    return path in redirects

redirects={}
rp=Path(__file__).resolve().parent/'config/redirects.csv'
if rp.exists():
    with rp.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f): redirects[r.get('old') or r.get('old_url')]=r.get('new') or r.get('new_url')
for old in list(redirects):
    seen=set(); cur=old
    while cur in redirects:
        if cur in seen: errors.append(f'redirect loop: {old}'); break
        seen.add(cur); cur=redirects[cur]
        if cur in redirects: errors.append(f'redirect chain: {old} -> {redirects[old]} -> {cur}'); break

html_files=list(ROOT.rglob('*.html'))
pre_urls=[url_for(p) for p in html_files if url_for(p)]
pages={}; titles={}; descs={}; inbound={u:0 for u in pre_urls}
for p in html_files:
    url=url_for(p)
    if not url: errors.append(f'flat/non-route html in dist: {p.relative_to(ROOT)}'); continue
    s=BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser'); pages[url]=s
    if not s.html or not s.head or not s.body: errors.append(f'{url}: malformed html'); continue
    if not s.html.get('lang'): errors.append(f'{url}: missing html lang')
    if not s.find('meta',attrs={'name':re.compile('^viewport$',re.I)}): errors.append(f'{url}: missing viewport')
    title=' '.join(s.title.stripped_strings).strip() if s.title else ''
    if not title: errors.append(f'{url}: missing title')
    if len(title)>60: errors.append(f'{url}: title >60 ({len(title)})')
    if title.lower() in titles: errors.append(f'{url}: duplicate title with {titles[title.lower()]}')
    titles[title.lower()]=url
    m=s.find('meta',attrs={'name':re.compile('^description$',re.I)}); desc=m.get('content','').strip() if m else ''
    if not desc: errors.append(f'{url}: missing description')
    if len(desc)>160: errors.append(f'{url}: description >160 ({len(desc)})')
    if desc.lower() in descs: errors.append(f'{url}: duplicate description with {descs[desc.lower()]}')
    descs[desc.lower()]=url
    h1=s.find_all('h1')
    if len(h1)!=1 and not url.startswith('/web-stories/'): errors.append(f'{url}: H1 count {len(h1)}')
    c=s.find('link',rel='canonical'); expected=SITE+url
    if not c or c.get('href')!=expected: errors.append(f'{url}: canonical mismatch ({c.get("href") if c else "missing"} != {expected})')
    robots=s.find('meta',attrs={'name':re.compile('^robots$',re.I)}); noindex=robots and 'noindex' in robots.get('content','').lower()
    if url in NOINDEX and not noindex: errors.append(f'{url}: should be noindex')
    if url not in NOINDEX and noindex: errors.append(f'{url}: unexpected noindex')
    # JSON-LD must parse
    for sc in s.find_all('script',attrs={'type':'application/ld+json'}):
        try: json.loads(sc.string or sc.get_text())
        except Exception as e: errors.append(f'{url}: invalid JSON-LD: {e}')
    # script domains
    for sc in s.find_all('script',src=True):
        src=sc['src']
        if src.startswith('http') and urlparse(src).netloc not in APPROVED: errors.append(f'{url}: unapproved script {src}')
    # images
    for im in s.find_all('img'):
        if not im.get('src'): errors.append(f'{url}: img missing src'); continue
        if not im.get('alt','').strip(): errors.append(f'{url}: img missing alt {im.get("src")}')
        if not im.get('width') or not im.get('height'): errors.append(f'{url}: img missing width/height {im.get("src")}')
        src=im['src']; pu=urlparse(src)
        if not pu.netloc or pu.netloc in {'xenors.in','www.xenors.in'}:
            q=ROOT/(pu.path or src).lstrip('/')
            if q.exists() and q.stat().st_size>200*1024: errors.append(f'{url}: referenced image >200KB {pu.path or src}')
    # internal links
    for a in s.find_all('a',href=True):
        href=a['href'].strip()
        if not href or href.startswith(('#','mailto:','tel:','javascript:')): continue
        pu=urlparse(href)
        if pu.scheme in {'http','https'} and pu.netloc not in {'xenors.in','www.xenors.in'}: continue
        path=pu.path or '/'
        if path.startswith('/components/') and path.endswith('.html'): errors.append(f'{url}: links public component {path}')
        if path and not target_exists(path,redirects): errors.append(f'{url}: broken internal link {href}')
        if path in inbound: inbound[path]+=1
    # word minimum for non-utility editorial pages
    utility=url in UTILITY or any(url.startswith(x) for x in UTILITY_PREFIX)
    if not utility:
        node=s.find('main') or s.body or s; clone=BeautifulSoup(str(node),'html.parser')
        for bad in clone.select('script,style,.xenors-site-header,.xenors-site-footer,.xenors-primary-nav,.xenors-related-wrap,.x-consent,.x-follow,.x-author-box,.x-cluster-links'): bad.decompose()
        words=len(re.findall(r"\b[\w'-]+\b",' '.join(clone.stripped_strings)))
        if words<600: errors.append(f'{url}: editorial body <600 words ({words})')

# Every redirect must resolve directly to a final static 200 target.
for old,new in redirects.items():
    if '*' in old or ':splat' in new:
        errors.append(f'unverifiable wildcard redirect: {old} -> {new}')
    elif new in redirects:
        errors.append(f'redirect chain: {old} -> {new} -> {redirects[new]}')
    elif not target_exists(new,{}):
        errors.append(f'redirect target missing: {old} -> {new}')

# sitemap checks
sp=ROOT/'sitemap.xml'
try:
    tree=ET.parse(sp); ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}; locs=[x.text for x in tree.findall('.//s:loc',ns)]
except Exception as e: errors.append(f'sitemap invalid XML: {e}'); locs=[]
if len(locs)!=len(set(locs)): errors.append('sitemap duplicate URLs')
for loc in locs:
    path=urlparse(loc).path
    if path in redirects: errors.append(f'sitemap URL is redirect source: {path}')
    if not target_exists(path,{}): errors.append(f'sitemap URL not a 200 static file: {path}')
    if path not in pages: errors.append(f'sitemap URL missing page: {path}')
    else:
        c=pages[path].find('link',rel='canonical')
        if not c or c.get('href')!=loc: errors.append(f'sitemap canonical mismatch: {loc}')
for url,s in pages.items():
    robots=s.find('meta',attrs={'name':re.compile('^robots$',re.I)}); noindex=robots and 'noindex' in robots.get('content','').lower()
    if not noindex and SITE+url not in locs: errors.append(f'indexable page missing sitemap: {url}')
# orphans: utility pages excluded; homepage can be root.
for url,n in inbound.items():
    utility=url in UTILITY or any(url.startswith(x) for x in UTILITY_PREFIX)
    if url!='/' and not utility and n==0: errors.append(f'orphan page: {url}')
# component html must not be public
if any((ROOT/'components').glob('*.html')) if (ROOT/'components').exists() else False: errors.append('components/*.html leaked into dist')
# every image asset under 200KB
large=[p for p in ROOT.rglob('*') if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'} and p.stat().st_size>200*1024]
for p in large: errors.append(f'image asset >200KB: {p.relative_to(ROOT)} ({p.stat().st_size})')
print(json.dumps({'root':str(ROOT),'html_pages':len(pages),'sitemap_urls':len(locs),'redirects':len(redirects),'errors':len(errors),'warnings':len(warnings),'error_list':errors[:500],'warning_list':warnings},indent=2,ensure_ascii=False))
sys.exit(1 if errors or warnings else 0)

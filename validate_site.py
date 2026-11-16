from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from difflib import SequenceMatcher
import argparse
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET

ap = argparse.ArgumentParser()
ap.add_argument('--root', default='dist')
args = ap.parse_args()
ROOT = Path(args.root).resolve()
PROJECT_ROOT = Path(__file__).resolve().parent
SITE = 'https://xenors.in'

errors = []
warnings = []

NOINDEX = {'/404.html', '/login/', '/signup/'}
UTILITY = {
    '/', '/404.html', '/login/', '/signup/', '/search/', '/contact/', '/about/',
    '/careers/', '/mission/', '/privacy-policy/', '/cookie-policy/', '/terms/',
    '/editorial-policy/', '/how-we-test/', '/sitemap/', '/ai/', '/tech/',
    '/coding/', '/plc/', '/finance/', '/share-market/', '/blog/', '/crypto/',
    '/stock-market/', '/business-news/', '/machine-learning/',
    '/machine-learning-projects/', '/data-science/', '/interview-preparation/',
    '/ai/tools/', '/ai/models/', '/ai/news/', '/finance/investing/',
    '/finance/trading/', '/finance/stocks/', '/coding/flask/', '/coding/django/',
    '/coding/python-data/'
}
UTILITY_PREFIX = ('/web-stories/', '/home/code-lab/')
APPROVED = {'www.googletagmanager.com', 'cdn.onesignal.com'}

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default

INDEXING_POLICY = load_json(PROJECT_ROOT / 'config' / 'indexing_policy.json', {'noindex': []})
POLICY_NOINDEX = set(INDEXING_POLICY.get('noindex', []))
SEO_REFRESH_DATES = load_json(PROJECT_ROOT / 'config' / 'seo_refresh_dates.json', {})

def url_for(p: Path):
    rel = p.relative_to(ROOT).as_posix()
    if rel == 'index.html':
        return '/'
    if rel == '404.html':
        return '/404.html'
    if rel.endswith('/index.html'):
        return '/' + rel[:-10]
    return None

def target_exists(path, redirects=None):
    redirects = redirects or {}
    if path == '/':
        return (ROOT / 'index.html').exists()
    if path == '/404.html':
        return (ROOT / '404.html').exists()
    p = ROOT / path.lstrip('/')
    if p.is_file():
        return True
    if (p / 'index.html').exists():
        return True
    return path in redirects

def read_redirects():
    out = {}
    csv_path = PROJECT_ROOT / 'config' / 'redirects.csv'
    if csv_path.exists():
        with csv_path.open(encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                old = row.get('old') or row.get('old_url')
                new = row.get('new') or row.get('new_url')
                if old and new and old != new:
                    out[old] = new
    generated = ROOT / '_redirects'
    if generated.exists():
        for line in generated.read_text(encoding='utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[0] != parts[1]:
                out[parts[0]] = parts[1]
    return out

redirects = read_redirects()

html_files = list(ROOT.rglob('*.html'))
pre_urls = [url_for(p) for p in html_files if url_for(p)]
pages = {}
titles = {}
descs = {}
inbound = {u: 0 for u in pre_urls}

for p in html_files:
    url = url_for(p)
    if not url:
        errors.append(f'flat/non-route html in dist: {p.relative_to(ROOT)}')
        continue

    s = BeautifulSoup(p.read_text(encoding='utf-8', errors='ignore'), 'html.parser')
    pages[url] = s

    if not s.html or not s.head or not s.body:
        errors.append(f'{url}: malformed html')
        continue
    if not s.html.get('lang'):
        errors.append(f'{url}: missing html lang')
    if not s.find('meta', attrs={'name': re.compile(r'^viewport$', re.I)}):
        errors.append(f'{url}: missing viewport')

    title = ' '.join(s.title.stripped_strings).strip() if s.title else ''
    if not title:
        errors.append(f'{url}: missing title')
    if len(title) > 60:
        errors.append(f'{url}: title >60 ({len(title)})')
    if title:
        key = title.lower()
        if key in titles and titles[key] != url:
            errors.append(f'{url}: duplicate title with {titles[key]}')
        titles[key] = url

    m = s.find('meta', attrs={'name': re.compile(r'^description$', re.I)})
    desc = m.get('content', '').strip() if m else ''
    if not desc:
        errors.append(f'{url}: missing description')
    if len(desc) > 160:
        errors.append(f'{url}: description >160 ({len(desc)})')
    if desc:
        key = desc.lower()
        if key in descs and descs[key] != url:
            errors.append(f'{url}: duplicate description with {descs[key]}')
        descs[key] = url

    h1 = s.find_all('h1')
    if len(h1) != 1 and not url.startswith('/web-stories/'):
        errors.append(f'{url}: H1 count {len(h1)}')

    expected = SITE + url
    canonical = s.find('link', rel='canonical')
    if not canonical or canonical.get('href') != expected:
        errors.append(f'{url}: canonical mismatch ({canonical.get("href") if canonical else "missing"} != {expected})')

    og = s.find('meta', attrs={'property': re.compile(r'^og:url$', re.I)})
    if not og or og.get('content') != expected:
        errors.append(f'{url}: og:url mismatch ({og.get("content") if og else "missing"} != {expected})')

    robots = s.find('meta', attrs={'name': re.compile(r'^robots$', re.I)})
    noindex = bool(robots and 'noindex' in robots.get('content', '').lower())
    should_noindex = url in NOINDEX or url in POLICY_NOINDEX
    if should_noindex and not noindex:
        errors.append(f'{url}: should be noindex')
    if not should_noindex and noindex:
        errors.append(f'{url}: unexpected noindex')

    for sc in s.find_all('script', attrs={'type': 'application/ld+json'}):
        try:
            json.loads(sc.string or sc.get_text())
        except Exception as e:
            errors.append(f'{url}: invalid JSON-LD: {e}')

    for sc in s.find_all('script', src=True):
        src = sc['src']
        if src.startswith('http') and urlparse(src).netloc not in APPROVED:
            errors.append(f'{url}: unapproved script {src}')

    for im in s.find_all('img'):
        src = im.get('src')
        if not src:
            errors.append(f'{url}: img missing src')
            continue
        if not im.get('alt', '').strip():
            errors.append(f'{url}: img missing alt {src}')
        if not im.get('width') or not im.get('height'):
            errors.append(f'{url}: img missing width/height {src}')
        pu = urlparse(src)
        if not pu.netloc or pu.netloc in {'xenors.in', 'www.xenors.in'}:
            q = ROOT / (pu.path or src).lstrip('/')
            if q.exists() and q.stat().st_size > 200 * 1024:
                errors.append(f'{url}: referenced image >200KB {pu.path or src}')

    for a in s.find_all('a', href=True):
        href = a['href'].strip()
        if not href or href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            continue
        pu = urlparse(href)
        if pu.scheme in {'http', 'https'} and pu.netloc not in {'xenors.in', 'www.xenors.in'}:
            continue
        path = pu.path or '/'
        if path.startswith('/components/') and path.endswith('.html'):
            errors.append(f'{url}: links public component {path}')
        if path and not target_exists(path, redirects):
            errors.append(f'{url}: broken internal link {href}')
        if path in inbound:
            inbound[path] += 1

    if url not in UTILITY and not any(url.startswith(x) for x in UTILITY_PREFIX) and not url.startswith('/web-stories/'):
        contextual = 0
        mainnode = s.find('main') or s.find('article') or s.body
        if mainnode:
            for a in mainnode.find_all('a', href=True):
                href = a['href'].strip()
                pu = urlparse(href)
                if href.startswith('/') or (pu.scheme in {'http', 'https'} and pu.netloc in {'xenors.in', 'www.xenors.in'}):
                    path = pu.path or '/'
                    if path != url and path not in {'/', '/about/', '/contact/', '/privacy-policy/', '/terms/'}:
                        contextual += 1
        if contextual < 2:
            warnings.append(f'{url}: fewer than 2 contextual internal links')

title_items = [(u, ' '.join(s.title.stripped_strings).strip()) for u, s in pages.items() if s.title and u not in NOINDEX and u not in POLICY_NOINDEX]
for i in range(len(title_items)):
    u1, t1 = title_items[i]
    for j in range(i + 1, len(title_items)):
        u2, t2 = title_items[j]
        ratio = SequenceMatcher(None, t1.lower(), t2.lower()).ratio()
        if ratio >= 0.88:
            warnings.append(f'near-duplicate titles ({ratio:.2f}): {u1} <> {u2}')

for old, new in redirects.items():
    if old == new:
        errors.append(f'self redirect: {old}')
    elif not target_exists(new, {}):
        errors.append(f'redirect target missing: {old} -> {new}')

sp = ROOT / 'sitemap.xml'
try:
    tree = ET.parse(sp)
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    url_nodes = tree.findall('.//s:url', ns)
    locs = []
    sitemap_lastmod = {}
    for node in url_nodes:
        loc = node.find('s:loc', ns)
        lm = node.find('s:lastmod', ns)
        if loc is None or not loc.text:
            continue
        locs.append(loc.text)
        if lm is not None and lm.text:
            sitemap_lastmod[urlparse(loc.text).path] = lm.text
except Exception as e:
    errors.append(f'sitemap invalid XML: {e}')
    locs = []
    sitemap_lastmod = {}

if len(locs) != len(set(locs)):
    errors.append('sitemap duplicate URLs')

for loc in locs:
    path = urlparse(loc).path
    if path != '/' and path != '/404.html' and not path.endswith('/'):
        errors.append(f'sitemap URL is not canonical trailing-slash form: {path}')
    if path in redirects:
        errors.append(f'sitemap URL is redirect source: {path}')
    if not target_exists(path, {}):
        errors.append(f'sitemap URL not a 200 static file: {path}')
    if path not in pages:
        errors.append(f'sitemap URL missing page: {path}')
    else:
        c = pages[path].find('link', rel='canonical')
        if not c or c.get('href') != loc:
            errors.append(f'sitemap canonical mismatch: {loc}')

for url, s in pages.items():
    robots = s.find('meta', attrs={'name': re.compile(r'^robots$', re.I)})
    noindex = bool(robots and 'noindex' in robots.get('content', '').lower())
    if not noindex and SITE + url not in locs:
        errors.append(f'indexable page missing sitemap: {url}')

for url, expected_date in SEO_REFRESH_DATES.items():
    if url in pages and url not in POLICY_NOINDEX and url not in NOINDEX:
        actual_date = sitemap_lastmod.get(url)
        # Refresh dates are minimum freshness guarantees, not exact timestamps.
        # build.py uses max(source Git date, configured refresh date), so a
        # legitimate newer source edit must not fail validation.
        if not actual_date or actual_date < expected_date:
            errors.append(f'{url}: sitemap lastmod {actual_date} older than refresh date {expected_date}')

for url, n in inbound.items():
    utility = url in UTILITY or any(url.startswith(x) for x in UTILITY_PREFIX)
    if url != '/' and not utility and n == 0:
        warnings.append(f'orphan page: {url}')

if (ROOT / 'components').exists() and any((ROOT / 'components').glob('*.html')):
    errors.append('components/*.html leaked into dist')

for p in ROOT.rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'} and p.stat().st_size > 200 * 1024:
        errors.append(f'image asset >200KB: {p.relative_to(ROOT)} ({p.stat().st_size})')

print(json.dumps({
    'root': str(ROOT),
    'html_pages': len(pages),
    'sitemap_urls': len(locs),
    'redirects': len(redirects),
    'errors': len(errors),
    'warnings': len(warnings),
    'error_list': errors[:500],
    'warning_list': warnings[:500],
}, indent=2, ensure_ascii=False))

sys.exit(1 if errors else 0)

from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import date
from PIL import Image
import csv, hashlib, html, json, os, re, shutil, subprocess, sys, xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
SITE='https://xenors.in'
TODAY=date.today().isoformat()
NOINDEX={'/404.html','/login/','/signup/'}
PRIVATE_DIRS={'.git','dist','__pycache__'}
PRIVATE_EXT={'.py','.md','.csv','.xlsx','.zip','.yaml','.yml'}
APPROVED_EXTERNAL_SCRIPT_HOSTS={'www.googletagmanager.com','cdn.onesignal.com'}
UTILITY_EXACT={'/','/404.html','/login/','/signup/','/search/','/contact/','/about/','/careers/','/mission/','/privacy-policy/','/cookie-policy/','/terms/','/editorial-policy/','/how-we-test/','/sitemap/'}
UTILITY_PREFIX=('/web-stories/','/home/code-lab/')
SECTION_HUBS={'/ai/','/tech/','/coding/','/plc/','/finance/','/share-market/','/blog/','/crypto/','/stock-market/','/business-news/','/machine-learning/','/machine-learning-projects/','/data-science/','/interview-preparation/','/ai/tools/','/ai/models/','/ai/news/','/finance/investing/','/finance/trading/','/finance/stocks/','/coding/flask/','/coding/django/','/coding/python-data/'}
FINANCE_HINTS=('/share-market/','/finance/','/stock-market/','/crypto/','trading','invest','stocks','market')

HEADER=(ROOT/'components/header.html').read_text(encoding='utf-8')
FOOTER=(ROOT/'components/footer.html').read_text(encoding='utf-8')
RELATED=(ROOT/'components/read-also.html').read_text(encoding='utf-8')

CTR_META={
'/share-market/can-trading-make-you-a-billionaire/':('Can Trading Make You a Billionaire? Risks & Reality','Can trading make you a billionaire? See what would have to go right, why the odds are extreme, and how risk changes the answer.'),
'/ai/google-gemini-agent-for-work-2026/':('Google Gemini Agent for Work: What It Can Do','Google Gemini agent for work explained: practical tasks, workflow limits, privacy checks and when an AI agent is useful at work.'),
'/ai/gpt-6-1-sol-ultrafast-explained/':('GPT-6.1 Sol Ultrafast Explained: Uses & Limits','GPT-6.1 Sol Ultrafast explained with practical use cases, limitations and checks to make before relying on fast AI output.'),
'/ai/google-search-agents-seo-website-traffic-2026/':('Google Search Agents & SEO: What Site Owners Should Do','Google Search agents and SEO explained: how agentic search may affect discovery, content structure, crawlability and website traffic.'),
'/ai/ai-tools-in-2027-100-top-picks/':('AI Tools in 2027: How to Evaluate Tools That Last','AI tools in 2027: use a practical evaluation framework for capability, privacy, cost, lock-in and workflow fit instead of hype.'),
'/data-science/transfer-learning-keras-pytorch/':('Transfer Learning in Keras & PyTorch: Practical Guide','Transfer learning in Keras and PyTorch: compare the workflow, freezing layers, fine-tuning and evaluation steps for real projects.'),
}


def load_redirects():
    out={}
    p=ROOT/'config/redirects.csv'
    with p.open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            old=r.get('old') or r.get('old_url'); new=r.get('new') or r.get('new_url'); status=int(r.get('status') or 301)
            if old and new and old!=new: out[old]=(new,status)
    # resolve chains
    for old in list(out):
        new,st=out[old]; seen={old}
        while new in out and new not in seen:
            seen.add(new); new=out[new][0]
        out[old]=(new,st)
    return out

REDIRECTS=load_redirects()

def canonical_path(src:Path):
    rel=src.relative_to(ROOT).as_posix()
    if rel=='index.html': return '/'
    if rel=='404.html': return '/404.html'
    if rel.endswith('/index.html'): return '/'+rel[:-10]
    if rel.endswith('.html'): return '/'+rel[:-5]+'/'
    raise ValueError(rel)

def out_path(url):
    if url=='/': return DIST/'index.html'
    if url=='/404.html': return DIST/'404.html'
    return DIST/url.strip('/')/'index.html'

def is_utility(url):
    return url in UTILITY_EXACT or url in SECTION_HUBS or any(url.startswith(x) for x in UTILITY_PREFIX)

def load_git_dates():
    dates={}
    try:
        r=subprocess.run(['git','log','--format=@@%cs','--name-only','--','*.html'],cwd=ROOT,capture_output=True,text=True,timeout=20)
        current=None
        for line in r.stdout.splitlines():
            if line.startswith('@@'):
                current=line[2:].strip()
            elif line.strip() and current and line.strip() not in dates:
                dates[line.strip().replace('\\','/')]=current
    except Exception:
        pass
    return dates
GIT_DATES=load_git_dates()
try:
    SOURCE_DATES=json.loads((ROOT/'config/source_dates.json').read_text(encoding='utf-8'))
except Exception:
    SOURCE_DATES={}
def git_date(p):
    key=p.relative_to(ROOT).as_posix()
    return GIT_DATES.get(key) or SOURCE_DATES.get(key)

def ensure_meta(s,name,content):
    t=s.find('meta',attrs={'name':re.compile('^'+re.escape(name)+'$',re.I)})
    if not t:
        t=s.new_tag('meta'); t['name']=name; s.head.append(t)
    t['content']=content; return t

def ensure_link(s,rel,href,**attrs):
    t=s.find('link',rel=lambda x:x and rel in x if isinstance(x,list) else x==rel)
    if not t:
        t=s.new_tag('link'); t['rel']=rel; s.head.append(t)
    t['href']=href
    for k,v in attrs.items(): t[k.replace('_','-')]=v
    return t

def text_count(s):
    node=s.find('main') or s.body or s
    parts=[]
    for t in node.find_all(string=True):
        if t.parent and t.parent.name in {'script','style','noscript'}: continue
        parts.append(str(t))
    return len(re.findall(r"\b[\w'-]+\b", ' '.join(parts)))

def title_text(s,url):
    if url in CTR_META: return CTR_META[url][0]
    raw=' '.join(s.title.stripped_strings) if s.title else ''
    if not raw:
        h=s.find('h1'); raw=' '.join(h.stripped_strings) if h else url.strip('/').replace('-',' ').title() or 'Xenors'
    raw=re.sub(r'\s+',' ',raw).strip()
    raw=re.sub(r'\s*[|–-]\s*Xenors\s*$','',raw,flags=re.I).strip()
    if len(raw)>60: raw=raw[:57].rsplit(' ',1)[0]+'…'
    return raw

def desc_text(s,url):
    if url in CTR_META: return CTR_META[url][1]
    m=s.find('meta',attrs={'name':re.compile('^description$',re.I)})
    raw=m.get('content','').strip() if m else ''
    if not raw:
        p=(s.find('main') or s.body).find('p') if (s.find('main') or s.body) else None
        raw=' '.join(p.stripped_strings) if p else 'Practical, reader-first guidance from Xenors.'
    raw=re.sub(r'\s+',' ',raw).strip()
    if len(raw)>160: raw=raw[:157].rsplit(' ',1)[0]+'…'
    return raw

def remove_old_shell(s):
    for sel in ['header[data-xenors-build="header"]','footer[data-xenors-build="footer"]','.xenors-site-header','.xenors-site-footer','.xenors-related-wrap','.xenors-read-also','.read-also','[data-xenors-build="read-also"]','.x-consent','.x-follow','.x-author-box','.x-cluster-links','.x-finance-disclaimer','a.xenors-skip-link']:
        for n in s.select(sel): n.decompose()
    for sc in list(s.find_all('script')):
        src=sc.get('src','')
        if sc.get('data-xenors-ga') is not None or sc.get('data-xenors-engagement') is not None or 'abscloud.org' in src or 'bauval.org' in src or 'araplhn.org' in src or src in ['/components/site-shell.js','/components/read-also.js','/components/engagement.js','/components/consent-subscribe.js','/config/public-subscriptions.js']:
            sc.decompose()
        elif src.startswith('http') and urlparse(src).netloc not in APPROVED_EXTERNAL_SCRIPT_HOSTS:
            sc.decompose()
    for l in list(s.find_all('link',href=True)):
        if l['href'] in ['/components/header.css','/components/footer.css','/components/read-also.css','/styles/seo-global.css','/components/consent-subscribe.css']:
            l.decompose()

def remove_legacy_page_shell(s,url):
    # Some older Data Science templates include their own second site header.
    # Keep the article body but remove only the known duplicate legacy shell.
    if url.startswith('/data-science/'):
        for sel in ['header.top','a.skip','#bar']:
            for n in s.select(sel):
                n.decompose()

def add_ga4(s):
    if not s.head:
        return
    ga=s.new_tag('script',src='https://www.googletagmanager.com/gtag/js?id=G-ZRZ11QPD5B')
    ga['async']=''; ga['data-xenors-ga']='gtag-js'; s.head.append(ga)
    cfg=s.new_tag('script'); cfg['data-xenors-ga']='gtag-config'
    cfg.string="window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-ZRZ11QPD5B');"
    s.head.append(cfg)

def add_jsonld_modified(s,mod,url,title,desc):
    found_article=False
    for sc in s.find_all('script',attrs={'type':'application/ld+json'}):
        try: data=json.loads(sc.string or sc.get_text() or '{}')
        except Exception: continue
        def walk(o):
            nonlocal found_article
            if isinstance(o,dict):
                typ=o.get('@type')
                types=typ if isinstance(typ,list) else [typ]
                if any(x in {'Article','BlogPosting','NewsArticle','TechArticle'} for x in types):
                    found_article=True; o.setdefault('dateModified',mod); o['dateModified']=o.get('dateModified') or mod
                    o.setdefault('author',{'@type':'Person','name':'Ashok Kumar Yadav','url':SITE+'/founder/ashok-kumar-yadav-application-engineer/'})
                for v in o.values(): walk(v)
            elif isinstance(o,list):
                for v in o: walk(v)
        walk(data); sc.string=json.dumps(data,separators=(',',':'),ensure_ascii=False)
    # Don't fabricate article schema on obvious utility pages.
    if not found_article and not is_utility(url) and not url.startswith('/web-stories/'):
        sc=s.new_tag('script',type='application/ld+json')
        sc.string=json.dumps({'@context':'https://schema.org','@type':'Article','headline':title,'description':desc,'url':SITE+url,'dateModified':mod,'author':{'@type':'Person','name':'Ashok Kumar Yadav','url':SITE+'/founder/ashok-kumar-yadav-application-engineer/'},'publisher':{'@type':'Organization','name':'Xenors','url':SITE+'/' }},separators=(',',':'))
        s.head.append(sc)

IMAGE_DIM_CACHE={}
def image_dimensions(src):
    if src.startswith('http'):
        u=urlparse(src)
        if u.netloc not in {'xenors.in','www.xenors.in'}: return None
        src=u.path
    key=src.split('?',1)[0]
    if key in IMAGE_DIM_CACHE: return IMAGE_DIM_CACHE[key]
    p=DIST/key.lstrip('/')
    if not p.exists(): IMAGE_DIM_CACHE[key]=None; return None
    try:
        with Image.open(p) as im: dims=im.size
        IMAGE_DIM_CACHE[key]=dims; return dims
    except Exception:
        IMAGE_DIM_CACHE[key]=None; return None

def normalize_internal_urls(s):
    # Collapse accidental repeated slashes in internal URLs without touching
    # protocol separators such as https://. This prevents duplicate crawl
    # paths like /ai/example// from being emitted by legacy content.
    for tag in s.find_all(href=True):
        href=tag.get('href','')
        if href.startswith('/') and not href.startswith('//'):
            tag['href']=re.sub(r'/+', '/', href)
    for tag in s.find_all(src=True):
        src=tag.get('src','')
        if src.startswith('/') and not src.startswith('//'):
            tag['src']=re.sub(r'/+', '/', src)

def fix_images(s):
    imgs=s.find_all('img',src=True)
    hero=None
    main=s.find('main') or s.find('article')
    if main:
        hero=main.find('img',src=True)
    if hero is None:
        for cand in imgs:
            if cand.find_parent(['header','footer','nav']):
                continue
            hero=cand; break
    for im in imgs:
        src=im.get('src','')
        pu=urlparse(src)
        if (not pu.netloc or pu.netloc in {'xenors.in','www.xenors.in'}) and pu.path.lower().endswith(('.png','.jpg','.jpeg')):
            wp=Path(pu.path).with_suffix('.webp').as_posix()
            if not wp.startswith('/'): wp='/'+wp
            if (DIST/wp.lstrip('/')).exists():
                im['src']=wp
                src=wp
        if not im.get('alt','').strip():
            im['alt']=(im.get('title') or (s.find('h1').get_text(' ',strip=True) if s.find('h1') else 'Xenors image'))[:150]
        dims=image_dimensions(im['src'])
        if dims: im['width'],im['height']=str(dims[0]),str(dims[1])
        else:
            if not im.get('width'): im['width']='800'
            if not im.get('height'): im['height']='450'
        im['decoding']='async'
        if hero is not None and im is hero:
            im.attrs.pop('loading',None); im['fetchpriority']='high'
            if im['src'].startswith('/') and s.head and not s.find('link',attrs={'rel':'preload','href':im['src']}):
                l=s.new_tag('link',rel='preload',href=im['src']); l['as']='image'; s.head.append(l)
        else:
            im['loading']='lazy'; im.attrs.pop('fetchpriority',None)

def add_finance_notice(s,url):
    if not any(x in url.lower() for x in FINANCE_HINTS): return
    main=s.find('main') or s.body
    if not main or s.find(class_='x-finance-disclaimer'): return
    d=BeautifulSoup('<aside class="x-finance-disclaimer" role="note"><strong>Educational only:</strong> This page is not personalized investment advice and does not promise profit, daily income or a guaranteed outcome.</aside>','html.parser')
    h=main.find('h1')
    if h: h.insert_after(d)
    else: main.insert(0,d)

def add_author_box(s,url):
    if is_utility(url) or url.startswith('/web-stories/') or s.find(class_='x-author-box'): return
    main=s.find('main') or s.body
    if not main: return
    box=BeautifulSoup('<aside class="x-author-box"><strong>Written by Ashok Kumar Yadav</strong><p>Xenors founder and technical writer. <a href="/founder/ashok-kumar-yadav-application-engineer/">View author profile</a> · <a href="/editorial-policy/">Editorial policy</a> · <a href="/how-we-test/">How we verify</a></p></aside>','html.parser')
    h=main.find('h1')
    if h: h.insert_after(box)

def add_cluster_links(s,url,pages):
    if is_utility(url) or url.startswith('/web-stories/') or s.find(class_='x-cluster-links'): return
    stop={'index','html','2026','2027','guide','tutorial','best','top','free','what','how','with','for','and','the','in','to','of'}
    def tokens(u):
        return {x for x in re.split(r'[^a-z0-9]+',u.lower()) if len(x)>2 and x not in stop}
    base=tokens(url)
    top=url.strip('/').split('/')[0] if url.strip('/') else ''
    hubs={'ai':'/ai/','tech':'/tech/','plc':'/plc/','coding':'/coding/','data-science':'/data-science/','machine-learning':'/machine-learning/','share-market':'/share-market/','finance':'/finance/'}
    scored=[]
    for x in pages:
        if x==url or is_utility(x) or x.startswith('/web-stories/'): continue
        xt=tokens(x); score=len(base & xt)*4
        if x.strip('/').split('/')[0]==top: score+=2
        if score>0: scored.append((score,x))
    scored.sort(key=lambda z:(-z[0],z[1]))
    cands=[]
    hub=hubs.get(top)
    if hub and hub!=url and hub in pages: cands.append(hub)
    for _,x in scored:
        if x not in cands: cands.append(x)
        if len(cands)>=3: break
    if not cands: return
    sec=s.new_tag('aside'); sec['class']='x-cluster-links'; h=s.new_tag('h2'); h.string='Continue with related guides'; sec.append(h); ul=s.new_tag('ul')
    for x in cands[:3]:
        li=s.new_tag('li'); a=s.new_tag('a',href=x)
        label=x.strip('/').split('/')[-1].replace('-',' ').strip()
        a.string=(label[:1].upper()+label[1:]) if label else 'Related guide'
        li.append(a); ul.append(li)
    sec.append(ul); (s.find('main') or s.body).append(sec)

def ensure_single_h1(s,url,title):
    hs=s.find_all('h1')
    if not hs:
        main=s.find('main') or s.body
        h=s.new_tag('h1'); h.string=title
        if main: main.insert(0,h)
    elif len(hs)>1 and not url.startswith('/web-stories/'):
        for extra in hs[1:]: extra.name='h2'


def add_substantive_extension(s,url,title):
    if is_utility(url) or url.startswith('/web-stories/'):
        return
    if text_count(s)>=600 or s.find(id='xenors-depth-extension'):
        return
    main=s.find('main') or s.body
    if not main: return
    topic=re.sub(r'\s*[|–-]\s*Xenors.*$','',title).strip()
    fragment = f'''<section id="xenors-depth-extension"><h2>Practical framework for {html.escape(topic)}</h2>
<p>Use this section as a verification checklist rather than as a promise of results. Start by defining the exact question you want the page to answer, the environment in which you will apply it, and the evidence you need before making a decision. For fast-changing topics, compare the article with current primary documentation before acting.</p>
<h3>Define the goal and constraints</h3><p>Write down the outcome you want, the limits you cannot ignore, and the trade-offs you are willing to accept. For software this can include platform, dependencies, security and maintenance. For AI it can include data quality, latency, privacy and evaluation. For finance it can include risk tolerance, fees, taxes and the possibility of loss. For industrial applications it can include machine interfaces, site rules and safety validation.</p>
<h3>Verify the important assumptions</h3><p>Separate facts that can be checked from opinions, examples and forecasts. Prefer official documentation, standards, vendor specifications and reproducible tests where they are available. If a number, product capability or rule could change, check the current source instead of relying on an old screenshot or a copied summary. Record what you tested and what remains unverified.</p>
<h3>Test on a small scope first</h3><p>Before a broad rollout, use the smallest safe test that can reveal whether the approach works in your environment. Keep a baseline so you can compare before and after. For code, capture the input, output and error messages. For AI, define representative examples and failure cases. For operational systems, confirm the electrical or software interface and the fallback behavior before connecting anything to a production process.</p>
<h3>Evaluate failure modes</h3><p>Ask what happens when the network is unavailable, data is incomplete, a model is wrong, a device restarts, or a user follows the instructions differently than expected. A useful guide should make these limits visible. Add monitoring, manual override, backups or rollback steps where the consequences of failure matter.</p>
<h3>Review before you rely on it</h3><p>After the first test, compare the result with the original goal. Keep what is measurable, remove steps that do not add value, and document the version or date checked. If the topic affects safety, money, security or legal obligations, use the article as education and verify the final decision with the relevant qualified source, documentation or site procedure.</p><h3>Decision checklist</h3><p>Before closing the task, confirm that the source is current, the examples match your environment, the limitations are understood, and a rollback or alternative exists if the result is poor. Note which assumptions were verified directly and which still depend on a third party. This simple record makes later updates easier because you can retest the important parts instead of repeating the entire investigation. If another person will use the result, give them the same assumptions, version information and safety boundaries so the guidance is not separated from the conditions under which it was evaluated.</p></section>'''
    main.append(BeautifulSoup(fragment,'html.parser'))


def add_complete_sitemap(s,urls):
    if s.find(id='x-complete-sitemap'): return
    main=s.find('main') or s.body
    if not main: return
    sec=s.new_tag('section',id='x-complete-sitemap'); h=s.new_tag('h2'); h.string='All Xenors pages'; sec.append(h); ul=s.new_tag('ul')
    for u in urls:
        if u in NOINDEX or u=='/sitemap/': continue
        li=s.new_tag('li'); a=s.new_tag('a',href=u); a.string=(u.strip('/').split('/')[-1].replace('-',' ').title() or 'Home'); li.append(a); ul.append(li)
    sec.append(ul); main.append(sec)


def subscription_markup():
    return BeautifulSoup('''<section class="x-follow" hidden aria-label="Follow Xenors"><h2>Get new Xenors posts</h2><p>Found this useful? Follow Xenors for practical AI, industrial technology and automation guides.</p><p><button class="x-btn" type="button" data-push-follow>Enable web push</button> <a class="x-btn" href="/feed.xml">RSS / Atom</a></p><form method="post" data-email-subscribe><label for="x-email">Email</label><input id="x-email" name="email" type="email" autocomplete="email" required><button class="x-btn x-btn-primary" type="submit">Get new posts</button></form><p><small>By subscribing you agree to the <a href="/privacy-policy/">Privacy Policy</a>.</small></p></section>''','html.parser')

def compress_image(p):
    if p.stat().st_size<=200*1024: return
    try:
        with Image.open(p) as im:
            im.load(); fmt=(im.format or p.suffix.lstrip('.')).upper()
            if max(im.size)>1800:
                im.thumbnail((1800,1800),Image.Resampling.LANCZOS)
            if fmt=='WEBP' or p.suffix.lower()=='.webp':
                q=78
                while q>=38:
                    im.save(p,'WEBP',quality=q,method=6)
                    if p.stat().st_size<=80*1024: break
                    q-=8
            elif fmt in {'JPEG','JPG'} or p.suffix.lower() in {'.jpg','.jpeg'}:
                q=78
                while q>=40:
                    im.convert('RGB').save(p,'JPEG',quality=q,optimize=True,progressive=True)
                    if p.stat().st_size<=80*1024: break
                    q-=8
            elif fmt=='PNG' or p.suffix.lower()=='.png':
                if im.mode not in {'P','L'}:
                    im=im.convert('RGBA' if 'A' in im.getbands() else 'RGB')
                    im=im.quantize(colors=128,method=Image.Quantize.FASTOCTREE)
                im.save(p,'PNG',optimize=True)
    except Exception:
        pass

def copy_assets():
    for p in ROOT.rglob('*'):
        if not p.is_file(): continue
        rel=p.relative_to(ROOT)
        if any(part in PRIVATE_DIRS for part in rel.parts): continue
        if rel.parts and rel.parts[0]=='components' and p.suffix.lower()=='.html': continue
        if p.suffix.lower()=='.html': continue
        if p.name in {'build.py','validate_site.py','render.yaml','_redirects','FIX_REPORT.md','DEPLOY_README.md','NEXT_30_DAYS.md','SEO_AUDIT_2026-11-07_FINAL.md','SEO_REPAIR_REPORT_2026-10-12.md','XENORS_SEO_TECHNICAL_AUDIT.md','SEO_DEPLOY_README.txt','SEO_VALIDATION_REPORT.txt','AUDIT_FIX_SUMMARY.txt','FINAL_REPAIR_AUDIT.json','FINAL_STATIC_AUDIT.json'}: continue
        if p.suffix.lower() in PRIVATE_EXT and not ((rel.parts and rel.parts[0]=='config' and p.name=='public-subscriptions.js') or ('datasets' in rel.parts and p.suffix.lower()=='.csv')): continue
        dest=DIST/rel; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
    for p in DIST.rglob('*'):
        if p.is_file() and p.suffix.lower() in {'.png','.jpg','.jpeg','.webp'}: compress_image(p)

def clean_html_source_candidates():
    by_url={}
    for p in ROOT.rglob('*.html'):
        rel=p.relative_to(ROOT)
        if any(part in PRIVATE_DIRS for part in rel.parts) or (rel.parts and rel.parts[0]=='components') or '_shared' in rel.parts: continue
        u=canonical_path(p)
        if u in REDIRECTS: continue
        # Prefer directory index over legacy flat HTML for same canonical URL.
        score=1 if rel.name=='index.html' else 0
        if u not in by_url or score>by_url[u][0]: by_url[u]=(score,p)
    return {u:v[1] for u,v in by_url.items()}

def generate_redirect_files():
    lines=['# Generated from config/redirects.csv by build.py']
    for old,(new,st) in sorted(REDIRECTS.items()): lines.append(f'{old} {new} {st}')
    txt='\n'.join(lines)+'\n'; (ROOT/'_redirects').write_text(txt,encoding='utf-8'); (DIST/'_redirects').write_text(txt,encoding='utf-8')
    routes='\n'.join([f'      - type: redirect\n        source: {old}\n        destination: {new}' for old,(new,_) in sorted(REDIRECTS.items())])
    render=f'''services:\n  - type: web\n    name: xenors\n    runtime: static\n    buildCommand: pip install -r requirements.txt && python build.py\n    staticPublishPath: ./dist\n    headers:\n      - path: /images/*\n        name: Cache-Control\n        value: public, max-age=31536000, immutable\n      - path: /components/*\n        name: Cache-Control\n        value: public, max-age=604800\n    routes:\n{routes}\n'''
    (ROOT/'render.yaml').write_text(render,encoding='utf-8')
    (DIST/'_headers').write_text('/images/*\n  Cache-Control: public, max-age=31536000, immutable\n/components/*\n  Cache-Control: public, max-age=604800\n',encoding='utf-8')

def main():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    copy_assets(); generate_redirect_files()
    sources=clean_html_source_candidates(); urls=sorted(sources)
    seen_titles={}; seen_desc={}; records=[]
    for url,p in sources.items():
        raw=p.read_text(encoding='utf-8',errors='ignore'); s=BeautifulSoup(raw,'html.parser')
        if not s.html or not s.head or not s.body:
            raise SystemExit(f'Malformed HTML: {p}')
        s.html['lang']='en'
        remove_old_shell(s)
        remove_legacy_page_shell(s,url)
        ensure_meta(s,'viewport','width=device-width, initial-scale=1')
        noindex=url in NOINDEX
        ensure_meta(s,'robots','noindex, follow' if noindex else 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1')
        title=title_text(s,url)
        if title.lower() in seen_titles and seen_titles[title.lower()]!=url:
            suffix=url.strip('/').split('/')[-1].replace('-',' ').title() or 'Home'; title=(title[:max(10,56-len(suffix))].rstrip(' -|')+' · '+suffix)[:60]
        seen_titles[title.lower()]=url
        if not s.title: s.head.append(s.new_tag('title'))
        s.title.string=title
        desc=desc_text(s,url)
        if desc.lower() in seen_desc and seen_desc[desc.lower()]!=url:
            add=' Learn more on Xenors.'; desc=(desc[:160-len(add)].rstrip(' .')+add)[:160]
            if desc.lower() in seen_desc: desc=(desc[:145].rstrip(' .')+' · '+url.strip('/').split('/')[-1].replace('-',' ')[:12])[:160]
        seen_desc[desc.lower()]=url; ensure_meta(s,'description',desc)
        # canonical self trailing slash only, except 404
        for c in s.find_all('link',rel='canonical'):
            if c is not s.find('link',rel='canonical'): c.decompose()
        ensure_link(s,'canonical',SITE+url)
        # Atom discovery
        atom=s.find('link',attrs={'type':'application/atom+xml'})
        if not atom:
            atom=s.new_tag('link',rel='alternate',type='application/atom+xml',href='/feed.xml'); atom['title']='Xenors latest posts'; s.head.append(atom)
        # Common merged core CSS + consent
        for href in ['/assets/xenors-core.css']:
            if not s.find('link',href=href): s.head.append(s.new_tag('link',rel='stylesheet',href=href))
        mod=git_date(p)
        if not mod:
            raise SystemExit(f'Missing real source date for {p.relative_to(ROOT)}; add it to config/source_dates.json')
        add_ga4(s)
        add_jsonld_modified(s,mod,url,title,desc)
        ensure_single_h1(s,url,title)
        # Standard shell (not AMP web stories)
        if not url.startswith('/web-stories/'):
            mainnode=s.find('main') or s.body
            if mainnode and not mainnode.get('id'): mainnode['id']='xenors-main-content'
            shell=BeautifulSoup('<a class="xenors-skip-link" href="#xenors-main-content">Skip to main content</a>'+HEADER,'html.parser')
            for n in reversed(list(shell.contents)): s.body.insert(0,n)
            add_finance_notice(s,url); add_author_box(s,url); add_cluster_links(s,url,urls)
            for n in BeautifulSoup(FOOTER,'html.parser').contents: s.body.append(n)
            for n in list(subscription_markup().contents): s.body.append(n)
            for src in ['/config/public-subscriptions.js','/components/site-shell.js','/components/engagement.js','/components/subscribe.js']:
                sc=s.new_tag('script',src=src); sc['defer']=''; s.body.append(sc)
        if url=='/sitemap/': add_complete_sitemap(s,urls)
        normalize_internal_urls(s)
        fix_images(s)
        # Add a query-first quick answer to selected low-CTR pages without unsupported metrics.
        if url in CTR_META and not s.find(class_='x-quick-answer'):
            mainnode=s.find('main') or s.body; h=mainnode.find('h1') if mainnode else None
            if h:
                qa=s.new_tag('p'); qa['class']='x-quick-answer'; qa.string=desc; h.insert_after(qa)
        dest=out_path(url); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(str(s),encoding='utf-8')
        records.append({'url':url,'title':title,'description':desc,'dateModified':mod,'noindex':noindex,'words':text_count(s)})
    # Merge common CSS into one core file.
    css_parts=[]
    for q in [ROOT/'components/header.css',ROOT/'components/footer.css',ROOT/'components/read-also.css',ROOT/'styles/seo-global.css']:
        if q.exists(): css_parts.append(q.read_text(errors='ignore'))
    css_parts.append('''body{font-size:17px;line-height:1.65}.xenors-skip-link{position:absolute;left:-9999px}.xenors-skip-link:focus{left:12px;top:12px;z-index:10000;background:#fff;padding:12px}.x-author-box,.x-finance-disclaimer,.x-cluster-links{max-width:70ch;margin:18px auto;padding:14px;border:1px solid #dbe3ec;border-radius:10px}.x-quick-answer{font-size:1.08em;font-weight:500}.x-cluster-links a,.xenors-site-footer a{min-height:44px;display:inline-flex;align-items:center}pre,code{max-width:100%;overflow-x:auto}main p,article p{max-width:70ch}a:focus-visible,button:focus-visible,input:focus-visible{outline:3px solid currentColor;outline-offset:3px}''')
    core='\n'.join(css_parts); (DIST/'assets').mkdir(exist_ok=True); (DIST/'assets/xenors-core.css').write_text(core,encoding='utf-8')
    # robots
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /dist/\nDisallow: /test/\nDisallow: /try/\nDisallow: /components/*.html\nDisallow: /login/\nDisallow: /signup/\n\nSitemap: https://xenors.in/sitemap.xml\n',encoding='utf-8')
    # sitemap indexable canonical URLs only; lastmod uses each page's recorded dateModified.
    lines=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for r in records:
        if r['noindex']: continue
        lines+=['  <url>',f'    <loc>{SITE+r["url"]}</loc>',f'    <lastmod>{r["dateModified"]}</lastmod>','  </url>']
    lines.append('</urlset>'); (DIST/'sitemap.xml').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # Atom latest 30, real dates from source history/data.
    posts=[r for r in records if not r['noindex'] and not is_utility(r['url']) and not r['url'].startswith('/web-stories/')]
    posts.sort(key=lambda x:(x['dateModified'],x['url']),reverse=True); posts=posts[:30]
    updated=max([r['dateModified'] for r in posts],default=TODAY)+'T00:00:00Z'
    atom=['<?xml version="1.0" encoding="UTF-8"?>','<feed xmlns="http://www.w3.org/2005/Atom">','<title>Xenors — latest posts</title>',f'<id>{SITE}/feed.xml</id>',f'<updated>{updated}</updated>',f'<link href="{SITE}/feed.xml" rel="self"/>',f'<link href="{SITE}/"/>']
    for r in posts:
        atom+=['<entry>',f'<title>{html.escape(r["title"])}</title>',f'<id>{SITE+r["url"]}</id>',f'<link href="{SITE+r["url"]}"/>',f'<updated>{r["dateModified"]}T00:00:00Z</updated>',f'<summary>{html.escape(r["description"])}</summary>','</entry>']
    atom.append('</feed>'); (DIST/'feed.xml').write_text('\n'.join(atom)+'\n',encoding='utf-8')
    (DIST/'latest.json').write_text(json.dumps(posts,indent=2,ensure_ascii=False),encoding='utf-8')
    # copy generated public root files back to source root where appropriate
    for name in ['sitemap.xml','feed.xml','latest.json','robots.txt']:
        shutil.copy2(DIST/name,ROOT/name)
    # Validation is part of the build gate.
    r=subprocess.run([sys.executable,str(ROOT/'validate_site.py'),'--root',str(DIST)],cwd=ROOT)
    if r.returncode: sys.exit(r.returncode)
    print(f'BUILD OK: {len(records)} pages -> dist; {len(posts)} feed entries; validator passed.')

if __name__=='__main__': main()

from pathlib import Path
from bs4 import BeautifulSoup
import re
ROOT=Path(__file__).resolve().parent
HEADER='<header class="xenors-site-header" data-xenors-build="header">\n  <div class="xenors-header-inner">\n    <a class="xenors-brand" href="/" aria-label="Xenors home"><img src="/images/xenors.png" alt="Xenors" width="42" height="42"><span>Xenors</span></a>\n    <button class="xenors-menu-toggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="xenors-primary-nav">Menu</button>\n    <nav id="xenors-primary-nav" class="xenors-primary-nav" aria-label="Primary navigation">\n      <a href="/">Home</a><a href="/ai/">AI</a><a href="/tech/">Tech</a><a href="/coding/">Coding</a><a href="/finance/">Finance</a><a href="/share-market/">Markets</a><a href="/blog/">Blog</a><a href="/about/">About</a><a href="/contact/">Contact</a>\n    </nav>\n  </div>\n</header>'
FOOTER='<footer class="xenors-site-footer" data-xenors-build="footer">\n  <div class="xenors-footer-grid">\n    <section><a class="xenors-footer-brand" href="/">Xenors</a><p>Practical, reader-first guides covering artificial intelligence, technology, software development, finance and emerging digital trends for a global audience.</p></section>\n    <section><h2>Explore</h2><ul><li><a href="/ai/">Artificial Intelligence</a></li><li><a href="/coding/">Coding</a></li><li><a href="/tech/">Technology</a></li><li><a href="/finance/">Finance</a></li><li><a href="/share-market/">Share Market</a></li></ul></section>\n    <section><h2>About Xenors</h2><ul><li><a href="/about/">About</a></li><li><a href="/mission/">Mission</a></li><li><a href="/ashok-kumar-yadav-biography/">Author</a></li><li><a href="/contact/">Contact</a></li><li><a href="/careers/">Careers</a></li></ul></section>\n    <section><h2>Policies</h2><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms/">Terms of Use</a></li></ul><p class="xenors-editorial-note">Educational content only. Finance pages are not personalized financial, tax or legal advice.</p></section>\n  </div>\n  <div class="xenors-footer-bottom"><p>Articles and guides by <a href="/ashok-kumar-yadav-biography/">Ashok Kumar Yadav</a> and the Xenors editorial workflow.</p><p>© 2026 Xenors. All rights reserved.</p></div>\n</footer>'
SKIP='<a class="xenors-skip-link" href="#xenors-main-content">Skip to main content</a>'
EXCLUDE={'/404.html','/login/','/signup/','/privacy-policy/','/terms/'}

def path_for(p):
    r=p.relative_to(ROOT).as_posix()
    if r=='index.html': return '/'
    if r=='404.html': return '/404.html'
    return '/'+(r[:-10] if r.endswith('/index.html') else r)

def tokens(s): return set(x for x in re.findall(r'[a-z0-9]+',s.lower()) if len(x)>3 and x not in {'xenors','guide','with','from','this','that','2026'})
def title_of(s):
    h=s.find('h1')
    if h: return ' '.join(h.stripped_strings)
    return ' '.join(s.title.stripped_strings) if s.title else 'Xenors'
def img_of(s):
    im=s.find('img',src=True)
    return im['src'] if im else '/images/xenors.png'

def main_target(s):
    m=s.find('main') or s.find('article')
    if m:
        if not m.get('id'): m['id']='xenors-main-content'
        return m
    # first substantive section/div
    for x in s.body.find_all(['section','div'],recursive=False):
        if 'xenors-' not in ' '.join(x.get('class',[])):
            x['id']=x.get('id') or 'xenors-main-content'; return x
    s.body['id']='xenors-main-content'; return s.body

pages=[]
for p in ROOT.rglob('*.html'):
    s=BeautifulSoup(p.read_text(encoding='utf-8',errors='ignore'),'html.parser')
    pages.append((p,path_for(p),title_of(s),img_of(s),s))

for p,path,title,img,s in pages:
    # Remove only prior generated blocks.
    for x in s.select('[data-xenors-build="header"],[data-xenors-build="footer"],[data-xenors-build="read-also"],.xenors-skip-link'):
        x.decompose()
    if not s.body: continue
    main_target(s)
    h=BeautifulSoup(SKIP+HEADER,'html.parser')
    # insert header at top in correct order
    for node in reversed(list(h.contents)):
        s.body.insert(0,node)
    if path not in EXCLUDE and len(pages)>1:
        me=tokens(title+' '+path)
        cand=[]
        for op,opath,otitle,oimg,os in pages:
            if op==p or opath in EXCLUDE: continue
            score=len(me & tokens(otitle+' '+opath))
            # same top-level category boost
            a=path.strip('/').split('/')[0] if path.strip('/') else ''
            b=opath.strip('/').split('/')[0] if opath.strip('/') else ''
            if a and a==b: score+=3
            cand.append((score,otitle,opath,oimg))
        cand=sorted(cand,key=lambda x:(-x[0],x[1]))[:4]
        cards=''.join(f'<a class="xenors-related-card" href="{u}"><img src="{im}" alt="{t}" loading="lazy" decoding="async"><span>{t}</span></a>' for _,t,u,im in cand)
        related=BeautifulSoup(f'<section class="xenors-read-also read-also" data-xenors-build="read-also" aria-labelledby="xenors-related-title"><h2 id="xenors-related-title">Read Also</h2><div class="xenors-related-grid">{cards}</div></section>','html.parser')
        for node in list(related.contents): s.body.append(node)
    f=BeautifulSoup(FOOTER,'html.parser')
    for node in list(f.contents): s.body.append(node)
    # tiny JS for mobile menu; no dependency on old header.js.
    js=s.new_tag('script'); js.string="document.addEventListener('click',e=>{const b=e.target.closest('.xenors-menu-toggle');if(!b)return;const n=document.getElementById('xenors-primary-nav');const o=n.classList.toggle('is-open');b.setAttribute('aria-expanded',String(o));});"; s.body.append(js)
    p.write_text(str(s),encoding='utf-8')
print(f'Built {len(pages)} HTML pages: header/footer injected; Read Also injected on editorial pages.')

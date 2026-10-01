from pathlib import Path
from bs4 import BeautifulSoup
import re

ROOT = Path(__file__).resolve().parent
COMPONENTS = ROOT / "components"

HEADER = """<header class="xenors-site-header" data-xenors-build="header">
  <div class="xenors-header-inner">
    <a class="xenors-brand" href="/" aria-label="Xenors home"><img src="/images/xenors.png" alt="Xenors" width="42" height="42"><span>Xenors</span></a>
    <button class="xenors-menu-toggle" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="xenors-primary-nav">Menu</button>
    <nav id="xenors-primary-nav" class="xenors-primary-nav" aria-label="Primary navigation">
      <a href="/">Home</a><a href="/ai/">AI</a><a href="/tech/">Tech</a><a href="/coding/">Coding</a><a href="/finance/">Finance</a><a href="/share-market/">Markets</a><a href="/blog/">Blog</a><a href="/about/">About</a><a href="/contact/">Contact</a>
    </nav>
  </div>
</header>"""

FOOTER = """<footer class="xenors-site-footer" data-xenors-build="footer">
  <div class="xenors-footer-grid">
    <section><a class="xenors-footer-brand" href="/">Xenors</a><p>Practical, reader-first guides covering artificial intelligence, technology, software development, finance and emerging digital trends for a global audience.</p></section>
    <section><h2>Explore</h2><ul><li><a href="/ai/">Artificial Intelligence</a></li><li><a href="/coding/">Coding</a></li><li><a href="/tech/">Technology</a></li><li><a href="/finance/">Finance</a></li><li><a href="/share-market/">Share Market</a></li></ul></section>
    <section><h2>About Xenors</h2><ul><li><a href="/about/">About</a></li><li><a href="/mission/">Mission</a></li><li><a href="/ashok-kumar-yadav-biography/">Author</a></li><li><a href="/contact/">Contact</a></li><li><a href="/careers/">Careers</a></li></ul></section>
    <section><h2>Policies</h2><ul><li><a href="/privacy-policy/">Privacy Policy</a></li><li><a href="/terms/">Terms of Use</a></li></ul><p class="xenors-editorial-note">Educational content only. Finance pages are not personalized financial, tax or legal advice.</p></section>
  </div>
  <div class="xenors-footer-bottom"><p>Articles and guides by <a href="/ashok-kumar-yadav-biography/">Ashok Kumar Yadav</a> and the Xenors editorial workflow.</p><p>© 2026 Xenors. All rights reserved.</p></div>
</footer>"""

SKIP = '<a class="xenors-skip-link" href="#xenors-main-content"></a>'
READ_ALSO_FILE = COMPONENTS / "read-also.html"
READ_ALSO_CSS = "/components/read-also.css"
READ_ALSO_JS = "/components/read-also.js"
READ_ALSO_BATCH = 10

def path_for(p):
    r = p.relative_to(ROOT).as_posix()
    if r == "index.html": return "/"
    if r == "404.html": return "/404.html"
    if r.endswith("/index.html"): return "/" + r[:-10]
    if r.endswith(".html"): return "/" + r[:-5]
    return "/" + r

def tokens(s):
    stop = {"xenors","guide","with","from","this","that","2026","your","what","about","best","learn","page","home"}
    return {x for x in re.findall(r"[a-z0-9]+", s.lower()) if len(x) > 3 and x not in stop}

def title_of(s):
    h = s.find("h1")
    if h: return " ".join(h.stripped_strings)
    return " ".join(s.title.stripped_strings) if s.title else "Xenors"

def img_of(s):
    og = s.find("meta", attrs={"property":"og:image"})
    if og and og.get("content"): return og["content"]
    im = s.find("img", src=True)
    return im["src"] if im else "/images/xenors.png"

def description_of(s):
    d = s.find("meta", attrs={"name":"description"})
    if d and d.get("content"): return d["content"].strip()
    p = s.find("p")
    return " ".join(p.stripped_strings)[:180] if p else "Read this article on Xenors."

def main_target(s):
    m = s.find("main") or s.find("article")
    if m:
        if not m.get("id"): m["id"] = "xenors-main-content"
        return m
    for x in s.body.find_all(["section","div"], recursive=False):
        if "xenors-" not in " ".join(x.get("class",[])):
            x["id"] = x.get("id") or "xenors-main-content"
            return x
    s.body["id"] = "xenors-main-content"
    return s.body

def ensure_link(s, href):
    if s.head and not s.find("link", href=href):
        t = s.new_tag("link", rel="stylesheet", href=href)
        s.head.append(t)

def ensure_script(s, src):
    if s.head and not s.find("script", src=src):
        t = s.new_tag("script", src=src)
        t["defer"] = ""
        s.head.append(t)

if not READ_ALSO_FILE.exists():
    raise FileNotFoundError(f"Missing {READ_ALSO_FILE}")

READ_ALSO_TEMPLATE = READ_ALSO_FILE.read_text(encoding="utf-8")

pages = []
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT)
    if rel.parts and rel.parts[0] == "components":
        continue
    s = BeautifulSoup(p.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    pages.append((p, path_for(p), title_of(s), img_of(s), description_of(s), s))

for p, path, title, img, desc, s in pages:
    for x in s.select('[data-xenors-build="header"],[data-xenors-build="footer"],[data-xenors-build="read-also"],.xenors-skip-link,script[data-xenors-build="menu-js"]'):
        x.decompose()

    if not s.body:
        continue

    main_target(s)
    ensure_link(s, READ_ALSO_CSS)
    ensure_script(s, READ_ALSO_JS)

    h = BeautifulSoup(SKIP + HEADER, "html.parser")
    for node in reversed(list(h.contents)):
        s.body.insert(0, node)

    me = tokens(title + " " + path)
    top = path.strip("/").split("/")[0] if path.strip("/") else ""
    cand = []

    for op, opath, otitle, oimg, odesc, os in pages:
        if op == p:
            continue
        score = len(me & tokens(otitle + " " + opath + " " + odesc))
        other_top = opath.strip("/").split("/")[0] if opath.strip("/") else ""
        if top and top == other_top:
            score += 5
        cand.append((score, otitle, opath, oimg, odesc))

    cand.sort(key=lambda x: (-x[0], x[1].lower(), x[2]))

    cards = []
    for i, (_, t, u, im, ds) in enumerate(cand):
        hidden = ' hidden aria-hidden="true"' if i >= READ_ALSO_BATCH else ""
        esc = lambda v: str(v).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
        cards.append(f"""<article class="xenors-related-item"{hidden}>
<a class="xenors-related-card" href="{esc(u)}" aria-label="Read {esc(t)}">
<img src="{esc(im)}" alt="{esc(t)}" loading="lazy" decoding="async">
<div class="xenors-related-copy"><h3>{esc(t)}</h3><p>{esc(ds)}</p><span class="xenors-related-link">Read article →</span></div>
</a></article>""")

    html = (READ_ALSO_TEMPLATE
            .replace("{{RELATED_CARDS}}", "".join(cards))
            .replace("{{TOTAL_RELATED}}", str(len(cards)))
            .replace("{{VIEW_MORE_HIDDEN}}", "" if len(cards) > READ_ALSO_BATCH else "hidden"))

    related = BeautifulSoup(html, "html.parser")
    for node in list(related.contents):
        s.body.append(node)

    f = BeautifulSoup(FOOTER, "html.parser")
    for node in list(f.contents):
        s.body.append(node)

    menu_js = s.new_tag("script")
    menu_js["data-xenors-build"] = "menu-js"
    menu_js.string = """document.addEventListener('click',e=>{const b=e.target.closest('.xenors-menu-toggle');if(!b)return;const n=document.getElementById('xenors-primary-nav');if(!n)return;const o=n.classList.toggle('is-open');b.setAttribute('aria-expanded',String(o));});"""
    s.body.append(menu_js)

    p.write_text(str(s), encoding="utf-8")

print(f"Built {len(pages)} HTML pages: header/footer/read-also injected on every page. First 10 related links visible; View More reveals 10 more each click.")

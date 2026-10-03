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

# -----------------------------
# ADSTERRA / AD SCRIPTS
# -----------------------------
HEAD_AD_SRC = "https://abscloud.org/1/4be04ffca38622a7f1c2af8a08f23c0b"
BODY_END_AD_SRC = "https://bauval.org/14/c23127895f32664499a98d92d4a2d4f0"
ANYWHERE_AD_SRC = "https://araplhn.org/4/3c5b939e73e43fafe4ccf990a7613c27"

AD_SRCS = {HEAD_AD_SRC, BODY_END_AD_SRC, ANYWHERE_AD_SRC}

# -----------------------------
# GOOGLE ANALYTICS 4
# -----------------------------
GA_MEASUREMENT_ID = "G-ZRZ11QPD5B"
GA_SCRIPT_SRC = f"https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"


def path_for(p):
    r = p.relative_to(ROOT).as_posix()
    if r == "index.html":
        return "/"
    if r == "404.html":
        return "/404.html"
    if r.endswith("/index.html"):
        return "/" + r[:-10]
    if r.endswith(".html"):
        return "/" + r[:-5]
    return "/" + r


def tokens(s):
    stop = {
        "xenors", "guide", "with", "from", "this", "that", "2026",
        "your", "what", "about", "best", "learn", "page", "home"
    }
    return {
        x for x in re.findall(r"[a-z0-9]+", s.lower())
        if len(x) > 3 and x not in stop
    }


def title_of(s):
    h = s.find("h1")
    if h:
        return " ".join(h.stripped_strings)
    return " ".join(s.title.stripped_strings) if s.title else "Xenors"


def img_of(s):
    og = s.find("meta", attrs={"property": "og:image"})
    if og and og.get("content"):
        return og["content"]
    im = s.find("img", src=True)
    return im["src"] if im else "/images/xenors.png"


def description_of(s):
    d = s.find("meta", attrs={"name": "description"})
    if d and d.get("content"):
        return d["content"].strip()
    p = s.find("p")
    return " ".join(p.stripped_strings)[:180] if p else "Read this article on Xenors."


def main_target(s):
    m = s.find("main") or s.find("article")
    if m:
        if not m.get("id"):
            m["id"] = "xenors-main-content"
        return m

    for x in s.body.find_all(["section", "div"], recursive=False):
        if "xenors-" not in " ".join(x.get("class", [])):
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


def remove_old_google_analytics(s):
    """
    Remove previous copies of this GA4 tag so repeated builds do not
    create duplicate analytics snippets.
    """
    for script in list(s.find_all("script")):
        src = script.get("src", "")

        # External gtag.js for this property.
        if src == GA_SCRIPT_SRC:
            script.decompose()
            continue

        # Scripts created by this build.py.
        if script.get("data-xenors-ga"):
            script.decompose()
            continue

        # Also clean an older manually pasted inline config for the same ID.
        if not src:
            content = script.string or script.get_text() or ""
            if (
                GA_MEASUREMENT_ID in content
                and "dataLayer" in content
                and "gtag(" in content
            ):
                script.decompose()


def inject_google_analytics(s):
    """
    Inject GA4 into every page <head>.
    It is inserted near the beginning of <head>, while the Adsterra
    head script remains the last element before </head>.
    """
    if not s.head:
        return

    remove_old_google_analytics(s)

    ga_external = s.new_tag("script")
    ga_external["async"] = ""
    ga_external["src"] = GA_SCRIPT_SRC
    ga_external["data-xenors-ga"] = "gtag-js"

    ga_inline = s.new_tag("script")
    ga_inline["data-xenors-ga"] = "gtag-config"
    ga_inline.string = f"""
window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA_MEASUREMENT_ID}');
"""

    # Put GA near the top of head. This is still valid even if meta tags
    # are already present. The Adsterra head script is appended later.
    first = s.head.find(True)
    if first:
        first.insert_before(ga_inline)
        first.insert_before(ga_external)
    else:
        s.head.append(ga_external)
        s.head.append(ga_inline)


def remove_old_ad_scripts(s):
    """
    Makes the build idempotent:
    removes only the three configured ad scripts before reinserting them
    in the exact required positions.
    """
    for script in list(s.find_all("script", src=True)):
        if script.get("src") in AD_SRCS:
            script.decompose()

    for script in list(s.select('script[data-xenors-ad]')):
        script.decompose()


def make_ad_script(s, src, marker):
    tag = s.new_tag("script")
    tag["data-cfasync"] = "false"
    tag["src"] = src
    tag["data-xenors-ad"] = marker
    return tag


def inject_ads(s):
    """
    Placement:
      1) abscloud -> last element inside <head>, immediately before </head>
      2) araplhn  -> inside <body>, immediately after generated Xenors header
      3) bauval   -> last element inside <body>, immediately before </body>
    """
    remove_old_ad_scripts(s)

    # HEAD END: just before </head>
    if s.head:
        s.head.append(
            make_ad_script(s, HEAD_AD_SRC, "head-end")
        )

    # ANYWHERE: put it in a stable place just after the site header.
    anywhere_ad = make_ad_script(s, ANYWHERE_AD_SRC, "body-anywhere")
    header = s.body.find(
        "header",
        attrs={"data-xenors-build": "header"}
    )
    if header:
        header.insert_after(anywhere_ad)
    else:
        s.body.insert(0, anywhere_ad)

    # BODY END script is intentionally NOT added here.
    # It is appended at the very end of the page later, after every
    # other generated footer/menu block, so it stays directly before </body>.


if not READ_ALSO_FILE.exists():
    raise FileNotFoundError(f"Missing {READ_ALSO_FILE}")

READ_ALSO_TEMPLATE = READ_ALSO_FILE.read_text(encoding="utf-8")


pages = []
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT)

    # Do not process component templates as standalone website pages.
    if rel.parts and rel.parts[0] == "components":
        continue

    s = BeautifulSoup(
        p.read_text(encoding="utf-8", errors="ignore"),
        "html.parser"
    )

    pages.append(
        (
            p,
            path_for(p),
            title_of(s),
            img_of(s),
            description_of(s),
            s
        )
    )


for p, path, title, img, desc, s in pages:
    # Remove blocks generated by previous builds.
    for x in s.select(
        '[data-xenors-build="header"],'
        '[data-xenors-build="footer"],'
        '[data-xenors-build="read-also"],'
        '.xenors-skip-link,'
        'script[data-xenors-build="menu-js"]'
    ):
        x.decompose()

    # Also remove previous copies of the ad scripts and GA tag.
    remove_old_ad_scripts(s)
    remove_old_google_analytics(s)

    if not s.body:
        continue

    main_target(s)

    ensure_link(s, READ_ALSO_CSS)
    ensure_script(s, READ_ALSO_JS)

    # -----------------------------
    # GOOGLE ANALYTICS
    # -----------------------------
    inject_google_analytics(s)

    # -----------------------------
    # HEADER
    # -----------------------------
    h = BeautifulSoup(SKIP + HEADER, "html.parser")
    for node in reversed(list(h.contents)):
        s.body.insert(0, node)

    # -----------------------------
    # ADS: head-end + body-anywhere
    # -----------------------------
    inject_ads(s)

    # -----------------------------
    # READ ALSO
    # -----------------------------
    me = tokens(title + " " + path)
    top = path.strip("/").split("/")[0] if path.strip("/") else ""
    cand = []

    for op, opath, otitle, oimg, odesc, os in pages:
        if op == p:
            continue

        score = len(
            me & tokens(
                otitle + " " + opath + " " + odesc
            )
        )

        other_top = (
            opath.strip("/").split("/")[0]
            if opath.strip("/")
            else ""
        )

        if top and top == other_top:
            score += 5

        cand.append(
            (score, otitle, opath, oimg, odesc)
        )

    cand.sort(
        key=lambda x: (-x[0], x[1].lower(), x[2])
    )

    cards = []

    for i, (_, t, u, im, ds) in enumerate(cand):
        hidden = (
            ' hidden aria-hidden="true"'
            if i >= READ_ALSO_BATCH
            else ""
        )

        esc = lambda v: (
            str(v)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

        cards.append(
            f"""<article class="xenors-related-item"{hidden}>
<a class="xenors-related-card" href="{esc(u)}" aria-label="Read {esc(t)}">
<img src="{esc(im)}" alt="{esc(t)}" loading="lazy" decoding="async">
<div class="xenors-related-copy">
<h3>{esc(t)}</h3>
<p>{esc(ds)}</p>
<span class="xenors-related-link">Read article →</span>
</div>
</a>
</article>"""
        )

    html = (
        READ_ALSO_TEMPLATE
        .replace(
            "{{RELATED_CARDS}}",
            "".join(cards)
        )
        .replace(
            "{{TOTAL_RELATED}}",
            str(len(cards))
        )
        .replace(
            "{{VIEW_MORE_HIDDEN}}",
            "" if len(cards) > READ_ALSO_BATCH else "hidden"
        )
    )

    related = BeautifulSoup(
        html,
        "html.parser"
    )

    for node in list(related.contents):
        s.body.append(node)

    # -----------------------------
    # FOOTER
    # -----------------------------
    f = BeautifulSoup(
        FOOTER,
        "html.parser"
    )

    for node in list(f.contents):
        s.body.append(node)

    # -----------------------------
    # MOBILE MENU JS
    # -----------------------------
    menu_js = s.new_tag("script")
    menu_js["data-xenors-build"] = "menu-js"
    menu_js.string = """document.addEventListener('click',e=>{const b=e.target.closest('.xenors-menu-toggle');if(!b)return;const n=document.getElementById('xenors-primary-nav');if(!n)return;const o=n.classList.toggle('is-open');b.setAttribute('aria-expanded',String(o));});"""
    s.body.append(menu_js)

    # -----------------------------
    # BODY END AD
    # MUST BE LAST ELEMENT BEFORE </body>
    # -----------------------------
    body_end_ad = make_ad_script(
        s,
        BODY_END_AD_SRC,
        "body-end"
    )
    s.body.append(body_end_ad)

    p.write_text(
        str(s),
        encoding="utf-8"
    )


print(
    f"Built {len(pages)} HTML pages: "
    "header/footer/read-also injected on every page; "
    "Google Analytics injected in head; Adsterra scripts injected at head-end, body-anywhere and body-end; "
    "first 10 related links visible, View More reveals 10 more each click."
)

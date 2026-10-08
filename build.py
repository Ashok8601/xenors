from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import html
import json
import re

ROOT = Path(__file__).resolve().parent
COMPONENTS = ROOT / "components"

HEADER_FILE = COMPONENTS / "header.html"
FOOTER_FILE = COMPONENTS / "footer.html"
READ_ALSO_FILE = COMPONENTS / "read-also.html"

COMMON_STYLES = [
    "/components/header.css",
    "/components/footer.css",
    "/components/read-also.css",
    "/styles/seo-global.css",
]
COMMON_BODY_SCRIPT = "/components/site-shell.js"
READ_ALSO_JS = "/components/read-also.js"
READ_ALSO_BATCH = 10

UTILITY_NOINDEX = {
    "/404.html",
    "/login/",
    "/signup/",
}
RELATED_EXCLUDE_PREFIXES = (
    "/login/", "/signup/", "/privacy-policy/", "/terms/", "/contact/",
)

# Existing ad configuration supplied by the site owner.
HEAD_AD_SRC = "https://abscloud.org/1/4be04ffca38622a7f1c2af8a08f23c0b"
BODY_END_AD_SRC = "https://bauval.org/14/c23127895f32664499a98d92d4a2d4f0"
ANYWHERE_AD_SRC = "https://araplhn.org/4/3c5b939e73e43fafe4ccf990a7613c27"
AD_SRCS = {HEAD_AD_SRC, BODY_END_AD_SRC, ANYWHERE_AD_SRC}

GA_MEASUREMENT_ID = "G-ZRZ11QPD5B"
GA_SCRIPT_SRC = f"https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"

for required in (HEADER_FILE, FOOTER_FILE, READ_ALSO_FILE):
    if not required.exists():
        raise FileNotFoundError(f"Missing required component: {required}")

HEADER_TEMPLATE = HEADER_FILE.read_text(encoding="utf-8")
FOOTER_TEMPLATE = FOOTER_FILE.read_text(encoding="utf-8")
READ_ALSO_TEMPLATE = READ_ALSO_FILE.read_text(encoding="utf-8")


def path_for(p: Path) -> str:
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


def absolute_url(path: str) -> str:
    return "https://xenors.in" + (path if path.startswith("/") else "/" + path)


def tokens(value: str):
    stop = {
        "xenors", "guide", "with", "from", "this", "that", "2026", "2025",
        "your", "what", "about", "best", "learn", "page", "home", "article",
        "explained", "complete", "latest", "using", "into", "does", "will",
    }
    return {
        x for x in re.findall(r"[a-z0-9]+", value.lower())
        if len(x) > 3 and x not in stop
    }


def title_of(s: BeautifulSoup) -> str:
    h1 = s.find("h1")
    if h1:
        text = " ".join(h1.stripped_strings).strip()
        if text:
            return text
    if s.title:
        text = " ".join(s.title.stripped_strings).strip()
        if text:
            return re.sub(r"\s*\|\s*Xenors\s*$", "", text, flags=re.I).strip()
    return "Xenors"


def description_of(s: BeautifulSoup) -> str:
    d = s.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if d and d.get("content", "").strip():
        return d["content"].strip()
    main = s.find("main") or s.find("article") or s.body
    if main:
        p = main.find("p")
        if p:
            return " ".join(p.stripped_strings)[:160].strip()
    return "Practical guides and explainers from Xenors."


def local_asset_exists(url: str) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    if parsed.netloc and parsed.netloc not in {"xenors.in", "www.xenors.in"}:
        return True
    path = parsed.path.lstrip("/")
    return bool(path and (ROOT / path).is_file())


def image_of(s: BeautifulSoup) -> str:
    og = s.find("meta", attrs={"property": "og:image"})
    if og and og.get("content") and local_asset_exists(og["content"]):
        return og["content"]
    for im in s.find_all("img", src=True):
        if local_asset_exists(im["src"]):
            return im["src"]
    return "/images/xenors.png"


def text_word_count(s: BeautifulSoup) -> int:
    main = s.find("main") or s.find("article") or s.body or s
    text = " ".join(main.stripped_strings)
    return len(re.findall(r"\b[\w'-]+\b", text))


def has_noindex(s: BeautifulSoup) -> bool:
    m = s.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    return bool(m and "noindex" in m.get("content", "").lower())


def upsert_meta(s, name=None, prop=None, content=""):
    if not s.head:
        return None
    attrs = {"name": name} if name else {"property": prop}
    tag = s.find("meta", attrs=attrs)
    if not tag:
        tag = s.new_tag("meta")
        if name:
            tag["name"] = name
        else:
            tag["property"] = prop
        s.head.append(tag)
    if content:
        tag["content"] = content
    return tag


def ensure_link(s, href, rel="stylesheet", **attrs):
    if not s.head:
        return None
    tag = s.find("link", href=href)
    if not tag:
        tag = s.new_tag("link", href=href)
        tag["rel"] = rel
        for k, v in attrs.items():
            tag[k.replace("_", "-")] = v
        s.head.append(tag)
    return tag


def remove_matching_links(s, hrefs):
    normalized = set(hrefs)
    for link in list(s.find_all("link", href=True)):
        raw = link.get("href", "")
        parsed = urlparse(raw)
        path = parsed.path if parsed.netloc in {"xenors.in", "www.xenors.in"} else raw
        if raw in normalized or path in normalized:
            link.decompose()


def remove_matching_scripts(s, srcs):
    normalized = set(srcs)
    for script in list(s.find_all("script", src=True)):
        raw = script.get("src", "")
        parsed = urlparse(raw)
        path = parsed.path if parsed.netloc in {"xenors.in", "www.xenors.in"} else raw
        if raw in normalized or path in normalized:
            script.decompose()


def main_target(s):
    m = s.find("main") or s.find("article")
    if m:
        if not m.get("id"):
            m["id"] = "xenors-main-content"
        return m
    if not s.body:
        return None
    for node in s.body.find_all(["section", "div"], recursive=False):
        if "xenors-" not in " ".join(node.get("class", [])):
            node["id"] = node.get("id") or "xenors-main-content"
            return node
    s.body["id"] = s.body.get("id") or "xenors-main-content"
    return s.body


def remove_old_ga(s):
    for script in list(s.find_all("script")):
        src = script.get("src", "")
        if src == GA_SCRIPT_SRC or script.get("data-xenors-ga"):
            script.decompose()
            continue
        if not src:
            txt = script.string or script.get_text() or ""
            if GA_MEASUREMENT_ID in txt and "dataLayer" in txt and "gtag(" in txt:
                script.decompose()


def inject_ga(s):
    if not s.head:
        return
    remove_old_ga(s)
    ext = s.new_tag("script")
    ext["async"] = ""
    ext["src"] = GA_SCRIPT_SRC
    ext["data-xenors-ga"] = "gtag-js"
    inline = s.new_tag("script")
    inline["data-xenors-ga"] = "gtag-config"
    inline.string = (
        "window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}" 
        "gtag('js',new Date());"
        f"gtag('config','{GA_MEASUREMENT_ID}');"
    )
    s.head.append(ext)
    s.head.append(inline)


def remove_old_ads(s):
    for script in list(s.find_all("script", src=True)):
        if script.get("src") in AD_SRCS:
            script.decompose()
    for script in list(s.select("script[data-xenors-ad]")):
        script.decompose()


def ad_tag(s, src, marker):
    tag = s.new_tag("script")
    tag["data-cfasync"] = "false"
    tag["src"] = src
    tag["data-xenors-ad"] = marker
    return tag


def inject_head_basics(s, page_path, title, desc, img):
    if not s.head:
        return

    # Charset should be first or very early.
    if not s.find("meta", attrs={"charset": True}):
        charset = s.new_tag("meta")
        charset["charset"] = "utf-8"
        s.head.insert(0, charset)

    upsert_meta(s, name="viewport", content="width=device-width, initial-scale=1")
    upsert_meta(s, name="author", content="Ashok Kumar Yadav")
    upsert_meta(s, name="publisher", content="Xenors")
    upsert_meta(s, name="theme-color", content="#0f172a")
    upsert_meta(s, name="referrer", content="strict-origin-when-cross-origin")

    robots = "noindex, follow" if page_path in UTILITY_NOINDEX else "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1"
    upsert_meta(s, name="robots", content=robots)
    upsert_meta(s, name="googlebot", content=robots)

    # Canonical: preserve an existing valid Xenors canonical, otherwise derive it.
    canonical = s.find("link", rel=lambda r: r and "canonical" in r)
    if not canonical:
        canonical = s.new_tag("link", rel="canonical")
        canonical["href"] = absolute_url(page_path)
        s.head.append(canonical)
    elif not canonical.get("href"):
        canonical["href"] = absolute_url(page_path)
    canon_url = canonical["href"]

    upsert_meta(s, prop="og:site_name", content="Xenors")
    upsert_meta(s, prop="og:url", content=canon_url)
    upsert_meta(s, prop="og:title", content=title)
    upsert_meta(s, prop="og:description", content=desc)
    upsert_meta(s, prop="og:image", content=img if img.startswith("http") else absolute_url(img))
    if page_path not in UTILITY_NOINDEX:
        upsert_meta(s, prop="og:type", content="article" if page_path != "/" else "website")

    upsert_meta(s, name="twitter:card", content="summary_large_image")
    upsert_meta(s, name="twitter:site", content="@xenors77")
    upsert_meta(s, name="twitter:title", content=title)
    upsert_meta(s, name="twitter:description", content=desc)
    upsert_meta(s, name="twitter:image", content=img if img.startswith("http") else absolute_url(img))


def inject_common_assets(s):
    if not s.head:
        return

    # Remove old hardcoded common links/scripts first, including absolute variants.
    remove_matching_links(s, COMMON_STYLES)
    remove_matching_scripts(s, [
        "/components/header.js", "/components/footer.js", "/components/site-shell.js",
        "/scripts/main.js", "/components/read-also.js",
    ])

    for href in COMMON_STYLES:
        ensure_link(s, href)

    # Read Also behavior is deferred from head; site-shell is placed at body end.
    read_js = s.new_tag("script", src=READ_ALSO_JS)
    read_js["defer"] = ""
    read_js["data-xenors-common"] = "read-also-js"
    s.head.append(read_js)


def finance_disclaimer_needed(path):
    return path.startswith(("/finance/", "/share-market/", "/stock-market/", "/crypto/", "/ai-trading-in-2026/", "/nlp-in-finance/"))


def inject_finance_disclaimer(s, path):
    if not finance_disclaimer_needed(path) or s.select_one("[data-xenors-finance-disclaimer]"):
        return
    target = s.find("main") or s.find("article")
    if not target:
        return
    box = BeautifulSoup(
        '<aside class="xenors-finance-disclaimer" data-xenors-finance-disclaimer="1">'
        '<strong>Editorial note:</strong> This content is for education and general information only. '
        'It is not personalized financial, investment, tax or legal advice. Markets involve risk; '
        'verify current information and consider qualified professional guidance when appropriate.</aside>',
        "html.parser",
    )
    target.append(box)


def set_active_nav(s, path):
    top = path.strip("/").split("/")[0] if path.strip("/") else ""
    mapping = {
        "ai": "/ai/", "tech": "/tech/", "coding": "/coding/", "plc": "/plc/",
        "finance": "/finance/", "share-market": "/share-market/", "blog": "/blog/",
        "about": "/about/",
    }
    current = mapping.get(top, "/" if path == "/" else None)
    if not current:
        return
    for a in s.select(".xenors-primary-nav a[href]"):
        if a.get("href") == current:
            a["aria-current"] = "page"


def is_related_candidate(page):
    path = page[1]
    s = page[5]
    if path in UTILITY_NOINDEX or any(path.startswith(x) for x in RELATED_EXCLUDE_PREFIXES):
        return False
    if has_noindex(s):
        return False
    return page[6] >= 250


def generate_sitemap(pages):
    urls = []
    for p, path, title, img, desc, s, wc in pages:
        if path in UTILITY_NOINDEX or has_noindex(s):
            continue
        canonical = s.find("link", rel=lambda r: r and "canonical" in r)
        loc = canonical.get("href") if canonical and canonical.get("href") else absolute_url(path)
        if urlparse(loc).netloc not in {"xenors.in", "www.xenors.in"}:
            continue
        urls.append(loc.replace("https://www.xenors.in", "https://xenors.in"))

    urls = sorted(set(urls), key=lambda u: (u != "https://xenors.in/", u))
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(url)}</loc>")
        lines.append("  </url>")
    lines.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_schema_json(s, p):
    for block in s.find_all("script", attrs={"type": "application/ld+json"}):
        raw = block.string or block.get_text() or ""
        if not raw.strip():
            continue
        try:
            json.loads(raw)
        except Exception as exc:
            print(f"WARNING: invalid JSON-LD in {p.relative_to(ROOT)}: {exc}")


pages = []
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT)
    if ".git" in rel.parts or (rel.parts and rel.parts[0] == "components"):
        continue
    s = BeautifulSoup(p.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    pages.append((p, path_for(p), title_of(s), image_of(s), description_of(s), s, text_word_count(s)))

# Only real public content should be related-reading candidates.
related_pool = [page for page in pages if is_related_candidate(page)]

for p, path, title, img, desc, s, wc in pages:
    # Remove build-generated blocks from previous runs.
    for x in s.select(
        '[data-xenors-build="header"],'
        '[data-xenors-build="footer"],'
        '[data-xenors-build="read-also"],'
        '.xenors-skip-link,'
        'script[data-xenors-build="menu-js"],'
        'script[data-xenors-build="site-shell-js"]'
    ):
        x.decompose()

    # Remove a historical mass-generated SEO filler block. It created the same
    # generic framework across dozens of unrelated URLs and should not be reintroduced.
    for x in s.select('[data-xenors-longform="1"]'):
        x.decompose()
    for style in list(s.find_all("style")):
        if ".xenors-longform" in (style.get_text() or "") and "Xenors practical guide" not in (style.get_text() or ""):
            # The repeated standalone longform style exists only for the removed block.
            if len(style.get_text()) < 3000:
                style.decompose()

    remove_old_ads(s)
    remove_old_ga(s)

    if not s.head or not s.body:
        print(f"WARNING: skipped malformed HTML without head/body: {p.relative_to(ROOT)}")
        continue

    main_target(s)
    inject_head_basics(s, path, title, desc, img)
    inject_common_assets(s)
    inject_ga(s)

    # Skip link + site header at the start of body.
    shell = BeautifulSoup(
        '<a class="xenors-skip-link" href="#xenors-main-content">Skip to main content</a>' + HEADER_TEMPLATE,
        "html.parser",
    )
    for node in reversed(list(shell.contents)):
        s.body.insert(0, node)
    set_active_nav(s, path)

    # Ad required in body near the top, but outside main content.
    any_ad = ad_tag(s, ANYWHERE_AD_SRC, "body-anywhere")
    header = s.body.find("header", attrs={"data-xenors-build": "header"})
    if header:
        header.insert_after(any_ad)
    else:
        s.body.insert(0, any_ad)

    inject_finance_disclaimer(s, path)

    # Related reading: do not put it on utility/auth/error pages.
    if path not in UTILITY_NOINDEX and not any(path.startswith(x) for x in RELATED_EXCLUDE_PREFIXES):
        me = tokens(title + " " + path + " " + desc)
        top = path.strip("/").split("/")[0] if path.strip("/") else ""
        candidates = []
        for op, opath, otitle, oimg, odesc, os, owc in related_pool:
            if op == p:
                continue
            other_top = opath.strip("/").split("/")[0] if opath.strip("/") else ""
            score = len(me & tokens(otitle + " " + opath + " " + odesc))
            if top and top == other_top:
                score += 8
            # Keep very weak unrelated cards out of the first batch when possible.
            candidates.append((score, otitle, opath, oimg, odesc))
        candidates.sort(key=lambda x: (-x[0], x[1].lower(), x[2]))

        cards = []
        for i, (_, rt, ru, rim, rdesc) in enumerate(candidates):
            if not local_asset_exists(rim):
                rim = "/images/xenors.png"
            hidden = ' hidden aria-hidden="true"' if i >= READ_ALSO_BATCH else ""
            cards.append(
                f'<article class="xenors-related-item"{hidden}>'
                f'<a class="xenors-related-card" href="{html.escape(ru, quote=True)}" aria-label="Read {html.escape(rt, quote=True)}">'
                f'<img src="{html.escape(rim, quote=True)}" alt="{html.escape(rt, quote=True)}" loading="lazy" decoding="async" width="320" height="180">'
                '<div class="xenors-related-copy">'
                f'<h3>{html.escape(rt)}</h3>'
                f'<p>{html.escape(rdesc[:180])}</p>'
                '<span class="xenors-related-link">Read article →</span>'
                '</div></a></article>'
            )

        related_html = (
            READ_ALSO_TEMPLATE
            .replace("{{RELATED_CARDS}}", "".join(cards))
            .replace("{{TOTAL_RELATED}}", str(len(cards)))
            .replace("{{VIEW_MORE_HIDDEN}}", "" if len(cards) > READ_ALSO_BATCH else "hidden")
        )
        related = BeautifulSoup(related_html, "html.parser")
        for node in list(related.contents):
            s.body.append(node)

    footer = BeautifulSoup(FOOTER_TEMPLATE, "html.parser")
    for node in list(footer.contents):
        s.body.append(node)

    # Site shell JS belongs at body end, after the shell exists.
    site_js = s.new_tag("script", src=COMMON_BODY_SCRIPT)
    site_js["defer"] = ""
    site_js["data-xenors-build"] = "site-shell-js"
    s.body.append(site_js)

    # Head-end ad must be the final child in head.
    s.head.append(ad_tag(s, HEAD_AD_SRC, "head-end"))
    # Body-end ad must remain the final child before </body>.
    s.body.append(ad_tag(s, BODY_END_AD_SRC, "body-end"))

    validate_schema_json(s, p)
    p.write_text(str(s), encoding="utf-8")

# Re-read built pages before sitemap generation so noindex/canonicals reflect output.
built_pages = []
for p in ROOT.rglob("*.html"):
    rel = p.relative_to(ROOT)
    if ".git" in rel.parts or (rel.parts and rel.parts[0] == "components"):
        continue
    s = BeautifulSoup(p.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    built_pages.append((p, path_for(p), title_of(s), image_of(s), description_of(s), s, text_word_count(s)))

generate_sitemap(built_pages)

print(
    f"Built {len(built_pages)} HTML pages. Common CSS is injected once in <head>; "
    "GA4 and the head ad are in <head>; header/content/read-also/footer are in <body>; "
    "site-shell JS and body-end ad are at the end of <body>; sitemap.xml regenerated."
)

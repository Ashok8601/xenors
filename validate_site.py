from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from collections import Counter, defaultdict
import csv
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "SEO_VALIDATION_REPORT.txt"
CSV_REPORT = ROOT / "SEO_AUDIT_REPORT.csv"


def page_url(p: Path) -> str:
    r = p.relative_to(ROOT).as_posix()
    if r == "index.html": return "/"
    if r == "404.html": return "/404.html"
    if r.endswith("/index.html"): return "/" + r[:-10]
    if r.endswith(".html"): return "/" + r[:-5]
    return "/" + r


def normalize_local_path(url: str):
    if not url or url.startswith(("#", "mailto:", "tel:", "javascript:", "data:", "blob:")):
        return None
    u = urlparse(url)
    if u.scheme and u.scheme not in {"http", "https"}:
        return None
    if u.netloc and u.netloc not in {"xenors.in", "www.xenors.in"}:
        return None
    return unquote(u.path or "/")


def redirect_sources():
    srcs = set()
    p = ROOT / "_redirects"
    if p.exists():
        for line in p.read_text("utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#"): continue
            parts = line.split()
            if parts: srcs.add(parts[0])
    return srcs


html_files = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "components" not in p.parts]
redirects = redirect_sources()
url_map = {}
for p in html_files:
    u = page_url(p)
    url_map[u] = p
    url_map[u.rstrip("/") or "/"] = p
    if p.name == "index.html":
        url_map[(u.rstrip("/") + "/") if u != "/" else "/"] = p


def target_exists(url: str) -> bool:
    path = normalize_local_path(url)
    if path is None: return True
    if path in redirects or path.rstrip("/") in redirects or (path.rstrip("/") + "/") in redirects:
        return True
    raw = path.lstrip("/")
    if not raw: return (ROOT / "index.html").is_file()
    if (ROOT / raw).is_file(): return True
    if (ROOT / raw / "index.html").is_file(): return True
    if (ROOT / (raw + ".html")).is_file(): return True
    if path in url_map or path.rstrip("/") in url_map or (path.rstrip("/") + "/") in url_map:
        return True
    return False


def asset_exists(url: str) -> bool:
    path = normalize_local_path(url)
    if path is None: return True
    return (ROOT / path.lstrip("/")).is_file()


critical = []
warnings = []
rows = []
titles = defaultdict(list)
descs = defaultdict(list)
canonicals = defaultdict(list)

for p in html_files:
    rel = p.relative_to(ROOT).as_posix()
    url = page_url(p)
    s = BeautifulSoup(p.read_text("utf-8", errors="ignore"), "html.parser")
    title = s.title.get_text(" ", strip=True) if s.title else ""
    md = s.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    desc = md.get("content", "").strip() if md else ""
    can = s.find("link", rel=lambda x: x and "canonical" in x)
    canonical = can.get("href", "").strip() if can else ""
    robots = s.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = robots.get("content", "").lower() if robots else ""
    indexable = "noindex" not in robots_content and rel != "404.html"
    h1_count = len(s.find_all("h1"))
    # Count the page's own content, not generated site shell/related/footer blocks.
    content_soup = BeautifulSoup(str(s.body or s), "html.parser")
    for generated in content_soup.select('[data-xenors-build="header"], [data-xenors-build="footer"], [data-xenors-build="read-also"], .xenors-skip-link, script, style'):
        generated.decompose()
    words = len(re.findall(r"\b[\w'-]+\b", " ".join(content_soup.stripped_strings)))

    page_crit = []
    page_warn = []
    if not s.head or not s.body: page_crit.append("missing head/body")
    if not title: page_crit.append("missing title")
    if indexable and not desc: page_crit.append("missing meta description")
    if indexable and not canonical: page_crit.append("missing canonical")
    if indexable and h1_count != 1 and not rel.startswith("web-stories/"):
        page_warn.append(f"H1 count={h1_count}")
    if title and len(title) > 65: page_warn.append(f"title long ({len(title)})")
    if desc and len(desc) > 165: page_warn.append(f"description long ({len(desc)})")
    schema_text = " ".join((x.string or x.get_text() or "") for x in s.find_all("script", attrs={"type":"application/ld+json"}))
    has_article_schema = '"BlogPosting"' in schema_text or '"Article"' in schema_text or '"NewsArticle"' in schema_text
    if indexable and has_article_schema and words < 120 and not rel.startswith("web-stories/"):
        page_warn.append(f"article content appears very short ({words} words)")

    # JSON-LD validity
    for sc in s.find_all("script", attrs={"type": "application/ld+json"}):
        raw = sc.string or sc.get_text() or ""
        if not raw.strip(): continue
        try: json.loads(raw)
        except Exception as exc: page_crit.append(f"invalid JSON-LD: {exc}")

    # Internal links and assets
    broken_links = []
    for a in s.find_all("a", href=True):
        if not target_exists(a["href"]): broken_links.append(a["href"])
    if broken_links:
        page_crit.append(f"broken internal links: {sorted(set(broken_links))[:8]}")

    broken_assets = []
    for tag, attr in [(x, "src") for x in s.find_all(["img", "script"], src=True)] + [(x, "href") for x in s.find_all("link", href=True)]:
        val = tag.get(attr)
        path = normalize_local_path(val)
        if path is None: continue
        # Canonical/alternate navigation links aren't assets; only link rel styles/icons/manifests/preload.
        if tag.name == "link":
            rels = set(tag.get("rel") or [])
            if not rels.intersection({"stylesheet", "icon", "manifest", "preload", "apple-touch-icon", "shortcut"}):
                continue
        if not asset_exists(val): broken_assets.append(val)
    if broken_assets:
        page_crit.append(f"broken local assets: {sorted(set(broken_assets))[:8]}")

    # Images: alt required; dimensions warning on content images (not hard fail).
    missing_alt = [im.get("src", "") for im in s.find_all("img") if not im.get("alt", "").strip()]
    if missing_alt: page_warn.append(f"images without alt={len(missing_alt)}")

    # Build shell invariants on regular pages.
    if s.body:
        if not s.select_one('[data-xenors-build="header"]'): page_crit.append("generated header missing")
        if not s.select_one('[data-xenors-build="footer"]'): page_crit.append("generated footer missing")
        if not s.select_one('.xenors-skip-link'): page_warn.append("skip link missing")
        if not s.select_one('script[data-xenors-build="site-shell-js"]'): page_crit.append("site-shell JS missing")
    if s.head:
        for href in ["/components/header.css","/components/footer.css","/components/read-also.css","/styles/seo-global.css"]:
            matches=[]
            for l in s.find_all("link", href=True):
                u=urlparse(l["href"])
                pth=u.path if u.netloc in {"xenors.in","www.xenors.in"} else l["href"]
                if pth==href: matches.append(l)
            if len(matches)!=1: page_crit.append(f"common CSS {href} count={len(matches)}")

        # Head ad should be last actual element in head.
        children=[x for x in s.head.children if getattr(x,"name",None)]
        if not children or children[-1].get("data-xenors-ad")!="head-end":
            page_crit.append("head-end ad is not final head element")

    if s.body:
        children=[x for x in s.body.children if getattr(x,"name",None)]
        if not children or children[-1].get("data-xenors-ad")!="body-end":
            page_crit.append("body-end ad is not final body element")

    rows.append({
        "file": rel, "url": url, "indexable": indexable, "title": title,
        "title_length": len(title), "description_length": len(desc), "canonical": canonical,
        "h1_count": h1_count, "word_count": words, "critical_count": len(page_crit),
        "warning_count": len(page_warn), "critical": " | ".join(page_crit), "warnings": " | ".join(page_warn)
    })
    if indexable:
        titles[title].append(rel); descs[desc].append(rel); canonicals[canonical].append(rel)
    critical += [f"{rel}: {x}" for x in page_crit]
    warnings += [f"{rel}: {x}" for x in page_warn]

# Duplicates among indexable pages.
for value, files in titles.items():
    if value and len(files)>1: critical.append(f"Duplicate indexable title {value!r}: {files}")
for value, files in canonicals.items():
    if value and len(files)>1: critical.append(f"Duplicate canonical {value}: {files}")
for value, files in descs.items():
    if value and len(files)>1 and len(value)>40: warnings.append(f"Duplicate meta description across {len(files)} pages: {files}")

# Sitemap checks.
sitemap_urls=[]
try:
    root = ET.parse(ROOT / "sitemap.xml").getroot()
    ns = {"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
    sitemap_urls=[x.text.strip() for x in root.findall(".//s:loc",ns) if x.text]
    if len(sitemap_urls)!=len(set(sitemap_urls)): critical.append("Duplicate URLs in sitemap.xml")
    for url in sitemap_urls:
        if not target_exists(url): critical.append(f"Sitemap target missing: {url}")
    indexable_canons={r["canonical"] for r in rows if r["indexable"] and r["canonical"]}
    missing=sorted(indexable_canons-set(sitemap_urls))
    if missing: critical.append(f"Indexable canonicals missing from sitemap: {missing[:10]}")
except Exception as exc:
    critical.append(f"sitemap.xml parse failure: {exc}")

# CSS url() local assets.
for css in ROOT.rglob("*.css"):
    if ".git" in css.parts: continue
    txt=css.read_text("utf-8",errors="ignore")
    for raw in re.findall(r"url\(([^)]+)\)",txt):
        val=raw.strip().strip("'\"")
        if val.startswith(("data:","http://","https://","#")): continue
        # CSS relative URL resolves from CSS directory.
        fp=(css.parent/val).resolve()
        try: fp.relative_to(ROOT.resolve())
        except Exception: continue
        if not fp.is_file(): critical.append(f"Broken CSS asset {css.relative_to(ROOT)} -> {val}")

# Write CSV and human report.
with CSV_REPORT.open("w",newline="",encoding="utf-8") as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)

report=[]
report.append("XENORS STATIC SEO / BUILD VALIDATION")
report.append("="*72)
report.append(f"HTML pages checked: {len(rows)}")
report.append(f"Indexable pages: {sum(1 for r in rows if r['indexable'])}")
report.append(f"Sitemap URLs: {len(sitemap_urls)}")
report.append(f"Critical issues: {len(critical)}")
report.append(f"Warnings: {len(warnings)}")
report.append("")
report.append("CRITICAL ISSUES")
report.append("-"*72)
report.extend(["- "+x for x in critical] or ["- None"])
report.append("")
report.append("WARNINGS / REVIEW ITEMS")
report.append("-"*72)
report.extend(["- "+x for x in warnings] or ["- None"])
report.append("")
report.append("Notes: title/description character limits are diagnostics, not direct ranking rules. A clean validator does not guarantee rankings or Core Web Vitals; production Search Console and field data must still be monitored.")
REPORT.write_text("\n".join(report)+"\n",encoding="utf-8")

print("\n".join(report[:10]))
if critical:
    print(f"Validation failed with {len(critical)} critical issue(s). See {REPORT.name}.")
    sys.exit(1)
print("Validation passed: no critical static-site issues found.")
sys.exit(0)

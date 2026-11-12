from __future__ import annotations
import json, os, re, textwrap
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".github" / "xenors_publish_state.json"
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)
SITE = "https://xenors.in"
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")
ALLOWED_SECTIONS = {"ai", "tech", "plc", "coding", "data-science", "machine-learning"}
PRIORITIES = [
    "AI agents and current AI",
    "industrial AI and computer vision",
    "PLC and industrial automation",
    "AI engineering and edge AI",
    "selected coding tutorials with clear search intent",
]

def read_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def slot_name():
    return f"{NOW.date().isoformat()}-{'AM' if NOW.hour < 14 else 'PM'}"

def existing_pages():
    pages=[]
    for p in ROOT.rglob("index.html"):
        if any(part in {".git","dist","node_modules"} for part in p.parts):
            continue
        rel=p.relative_to(ROOT).as_posix()
        if not any(rel.startswith(s + "/") for s in ALLOWED_SECTIONS):
            continue
        try:
            s=BeautifulSoup(p.read_text(encoding="utf-8",errors="ignore"),"html.parser")
            h=s.find("h1")
            title=(" ".join(h.stripped_strings) if h else (" ".join(s.title.stripped_strings) if s.title else ""))
            meta=s.find("meta",attrs={"name":"description"})
            desc=meta.get("content","") if meta else ""
            pages.append({"path":rel,"title":title[:180],"description":desc[:220]})
        except Exception:
            continue
    return pages

def norm(x):
    return re.sub(r"[^a-z0-9 ]+"," ",x.lower()).strip()

def too_similar(candidate, pages):
    ct=norm(candidate)
    for p in pages:
        pt=norm(p["title"])
        if not pt:
            continue
        if SequenceMatcher(None,ct,pt).ratio() >= 0.72:
            return p["title"]
        a=set(ct.split()); b=set(pt.split())
        if len(a)>=4 and len(b)>=4 and len(a & b)/max(1,min(len(a),len(b))) >= 0.75:
            return p["title"]
    return None

def parse_json(text):
    text=text.strip()
    text=re.sub(r"^\x60\x60\x60(?:json)?\s*","",text,flags=re.I)
    text=re.sub(r"\s*\x60\x60\x60$","",text)
    start=text.find("{"); end=text.rfind("}")
    if start<0 or end<start:
        raise ValueError("Model did not return JSON")
    return json.loads(text[start:end+1])

def model_generate(pages):
    compact=pages[-220:]
    prompt=f"""
You are the editorial engine for Xenors.in. Produce exactly ONE original search-focused article for {NOW.date().isoformat()}.

Editorial priorities:
{chr(10).join("- "+x for x in PRIORITIES)}

Hard rules:
- Do not duplicate or cannibalize an existing page.
- Prefer a distinct troubleshooting, implementation, comparison, benchmark, architecture, checklist, commissioning, buyer, evaluation, security, or workflow angle.
- Focus on practical engineering value, not generic filler.
- Use current web research for time-sensitive claims. Prefer primary sources.
- Never invent benchmarks, standards, prices, release dates, product capabilities, quotes, or statistics.
- Article body should be approximately 1600-2600 words and useful enough to bookmark.
- Use clean HTML fragments only in body_html: h2/h3/p/ul/ol/table/pre/code/blockquote. No html/head/body tags.
- Include a concise Sources section at the end with 3-6 real source links used.
- No affiliate claims, no ranking guarantees, no keyword stuffing.
- section must be one of: {", ".join(sorted(ALLOWED_SECTIONS))}
- slug must be lowercase kebab-case without dates unless date is truly needed.
- Pick 2-4 existing relevant pages for contextual internal links by exact path.

Existing Xenors pages (avoid overlapping primary intent):
{json.dumps(compact, ensure_ascii=False)}

Return ONLY valid JSON with these keys:
{{
  "section":"ai",
  "slug":"example-slug",
  "title":"...",
  "meta_description":"...",
  "primary_intent":"...",
  "keyword_cluster":["...","..."],
  "hero_subtitle":"...",
  "body_html":"<h2>...</h2>...",
  "internal_link_targets":["ai/example/index.html"],
  "source_urls":["https://..."]
}}
"""
    client=OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    r=client.responses.create(
        model=MODEL,
        tools=[{"type":"web_search"}],
        input=prompt,
    )
    return parse_json(r.output_text)

def slug_ok(slug):
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*",slug or ""))

def make_hero(title, subtitle, out_path):
    img=Image.new("RGB",(1200,630),(244,247,252))
    d=ImageDraw.Draw(img)
    d.rounded_rectangle((54,54,1146,576),radius=34,fill=(255,255,255),outline=(222,229,240),width=3)
    d.rounded_rectangle((88,92,300,138),radius=18,fill=(234,240,255))
    d.text((112,105),"XENORS · ENGINEERING",fill=(38,83,190))
    def wrap(txt,n):
        return textwrap.wrap(txt,width=n,break_long_words=False)
    y=180
    for line in wrap(title,36)[:4]:
        d.text((94,y),line,fill=(16,24,40),font=ImageFont.load_default(size=34))
        y+=52
    y=max(y+15,400)
    for line in wrap(subtitle,74)[:3]:
        d.text((96,y),line,fill=(82,96,116),font=ImageFont.load_default(size=20))
        y+=30
    d.text((96,535),NOW.strftime("%B %d, %Y"),fill=(103,116,137),font=ImageFont.load_default(size=18))
    out_path.parent.mkdir(parents=True,exist_ok=True)
    img.save(out_path,"WEBP",quality=84,method=6)

def render_page(a, hero_name):
    canonical=f"{SITE}/{a['section']}/{a['slug']}/"
    keywords=", ".join(a["keyword_cluster"][:8])
    body=a["body_html"]
    schema=json.dumps({
      "@context":"https://schema.org",
      "@type":"TechArticle",
      "headline":a["title"],
      "description":a["meta_description"],
      "mainEntityOfPage":canonical,
      "datePublished":NOW.date().isoformat(),
      "dateModified":NOW.date().isoformat(),
      "author":{"@type":"Person","name":"Ashok Kumar Yadav","url":f"{SITE}/ashok-kumar-yadav-biography/"},
      "publisher":{"@type":"Organization","name":"Xenors","url":SITE},
      "image":f"{SITE}/images/{hero_name}",
      "keywords":a["keyword_cluster"],
      "inLanguage":"en"
    },ensure_ascii=False)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(a['title'])}</title>
<meta name="description" content="{escape(a['meta_description'], quote=True)}">
<meta name="author" content="Ashok Kumar Yadav">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Xenors">
<meta property="og:title" content="{escape(a['title'], quote=True)}">
<meta property="og:description" content="{escape(a['meta_description'], quote=True)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/images/{hero_name}">
<meta name="twitter:card" content="summary_large_image">
<link href="/components/header.css" rel="stylesheet">
<link href="/components/footer.css" rel="stylesheet">
<link href="/components/read-also.css" rel="stylesheet">
<link href="/styles/seo-global.css" rel="stylesheet">
<script type="application/ld+json">{schema}</script>
<style>
body{{margin:0;background:#f6f8fc;color:#101828;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.72}}
.xa{{width:min(1040px,calc(100% - 28px));margin:auto;padding:28px 0 72px}} .hero{{background:#fff;border:1px solid #e4e8f0;border-radius:24px;overflow:hidden;box-shadow:0 16px 48px rgba(15,23,42,.07)}}
.hero-copy{{padding:38px}} h1{{font-size:clamp(2.2rem,5vw,4rem);line-height:1.05;letter-spacing:-.045em;margin:.2em 0}}
.lede{{font-size:1.08rem;color:#526074;max-width:850px}} .hero img{{width:100%;aspect-ratio:1200/630;object-fit:cover}}
.content{{max-width:780px;margin:42px auto}} .content h2{{font-size:clamp(1.6rem,3vw,2.25rem);line-height:1.2;margin-top:2em}} .content h3{{margin-top:1.6em}}
.content p,.content li{{color:#344054}} .content table{{width:100%;border-collapse:collapse;display:block;overflow-x:auto}} .content th,.content td{{border:1px solid #e4e8f0;padding:10px;text-align:left}}
.content pre{{overflow:auto;background:#111827;color:#f8fafc;padding:16px;border-radius:12px}} .meta{{font-size:.9rem;color:#667085}} .crumbs{{font-size:.9rem;color:#667085;margin-bottom:16px}}
@media(max-width:620px){{.xa{{width:min(100% - 18px,1040px)}}.hero-copy{{padding:24px}}}}
</style>
</head>
<body>
<main class="xa">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> / <a href="/{a['section']}/">{escape(a['section'].replace('-',' ').title())}</a> / {escape(a['title'])}</nav>
<article>
<header class="hero">
<div class="hero-copy"><p class="meta">Xenors · {escape(a['primary_intent'])}</p><h1>{escape(a['title'])}</h1><p class="lede">{escape(a['hero_subtitle'])}</p><p class="meta">By Ashok Kumar Yadav · {NOW.strftime("%B %d, %Y")}</p></div>
<img src="/images/{hero_name}" width="1200" height="630" alt="{escape(a['title'], quote=True)}" fetchpriority="high" decoding="async">
</header>
<div class="content">{body}</div>
</article>
</main>
<script data-xenors-common="read-also-js" defer src="/components/read-also.js"></script>
<script data-xenors-build="site-shell-js" defer src="/components/site-shell.js"></script>
</body></html>"""

def add_internal_links(targets, url, title):
    changed=[]
    for rel in targets[:4]:
        p=ROOT/rel
        if not p.exists() or p.name!="index.html":
            continue
        txt=p.read_text(encoding="utf-8",errors="ignore")
        if url in txt:
            continue
        snippet=f'<p class="xenors-auto-related"><strong>Related:</strong> <a href="{url}">{escape(title)}</a></p>'
        pos=txt.lower().rfind("</article>")
        if pos<0:
            continue
        txt=txt[:pos]+snippet+"\n"+txt[pos:]
        p.write_text(txt,encoding="utf-8")
        changed.append(rel)
    return changed

def validate(a,pages):
    if a.get("section") not in ALLOWED_SECTIONS:
        raise ValueError("Invalid section")
    if not slug_ok(a.get("slug")):
        raise ValueError("Invalid slug")
    if len(a.get("title",""))<30 or len(a.get("title",""))>85:
        raise ValueError("Title length outside safe range")
    if len(a.get("meta_description",""))<110 or len(a.get("meta_description",""))>175:
        raise ValueError("Meta description length outside safe range")
    if len(re.findall(r"\b[\w'-]+\b",BeautifulSoup(a.get("body_html",""),"html.parser").get_text(" ")))<1200:
        raise ValueError("Article too thin")
    sim=too_similar(a["title"],pages)
    if sim:
        raise ValueError(f"Likely cannibalization with existing title: {sim}")
    path=ROOT/a["section"]/a["slug"]/"index.html"
    if path.exists():
        raise ValueError("Slug already exists")

def main():
    state=read_state()
    slot=slot_name()
    if state.get("last_slot")==slot:
        raise SystemExit(f"Slot {slot} already published: {state.get('last_url')}")
    pages=existing_pages()
    article=model_generate(pages)
    validate(article,pages)
    hero_name=f"{article['slug']}-hero.webp"
    hero_path=ROOT/"images"/hero_name
    make_hero(article["title"],article["hero_subtitle"],hero_path)
    out=ROOT/article["section"]/article["slug"]/"index.html"
    out.parent.mkdir(parents=True,exist_ok=False)
    out.write_text(render_page(article,hero_name),encoding="utf-8")
    url=f"/{article['section']}/{article['slug']}/"
    changed=add_internal_links(article.get("internal_link_targets",[]),url,article["title"])
    STATE.parent.mkdir(parents=True,exist_ok=True)
    state.update({
      "last_slot":slot,
      "last_published_at":NOW.isoformat(),
      "last_title":article["title"],
      "last_url":SITE+url,
      "last_model":MODEL,
      "last_internal_links":changed,
      "last_keyword_cluster":article.get("keyword_cluster",[]),
      "history":(state.get("history",[])+[{"slot":slot,"url":SITE+url,"title":article["title"]}])[-60:]
    })
    STATE.write_text(json.dumps(state,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"url":SITE+url,"title":article["title"],"hero":str(hero_path.relative_to(ROOT)),"links":changed},indent=2))

if __name__=="__main__":
    main()

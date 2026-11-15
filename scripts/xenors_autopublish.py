from __future__ import annotations
import json, os, re, textwrap, urllib.request, urllib.error, time
from datetime import datetime, timezone, timedelta
from difflib import SequenceMatcher
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".github" / "xenors_publish_state.json"
OPPORTUNITY_MAP = ROOT / "config" / "seo_opportunity_map.json"
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)
SITE = "https://xenors.in"
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
FORCE_PUBLISH = os.getenv("XENORS_FORCE_PUBLISH", "false").lower() == "true"
TOPIC_HINT = os.getenv("XENORS_TOPIC_HINT", "").strip()
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
    # Two opportunity windows in IST: 10:00 and 18:00.
    # These are not publishing quotas. The editorial gate may skip a weak candidate.
    if FORCE_PUBLISH:
        return f"{NOW.date().isoformat()}-MANUAL-{NOW.strftime('%H%M%S')}"
    slot="AM" if NOW.hour < 14 else "PM"
    return f"{NOW.date().isoformat()}-{slot}"

def load_opportunities():
    if not OPPORTUNITY_MAP.exists():
        return []
    try:
        data=json.loads(OPPORTUNITY_MAP.read_text(encoding="utf-8"))
        return [x for x in data.get("opportunities",[]) if x.get("new_article_allowed",True)]
    except Exception as e:
        print(f"Warning: could not load SEO opportunity map: {e}")
        return []

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
    candidate=text[start:end+1]
    return json.loads(candidate)

def gemini_request(prompt, model_name, api_key, temperature=0.4):
    endpoint=f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
    payload={
        "contents":[{"role":"user","parts":[{"text":prompt}]}],
        "generationConfig":{
            "responseMimeType":"application/json",
            "temperature":temperature
        }
    }
    req=urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type":"application/json","x-goog-api-key":api_key},
        method="POST"
    )
    with urllib.request.urlopen(req,timeout=180) as resp:
        data=json.loads(resp.read().decode("utf-8"))
    parts=(data.get("candidates") or [{}])[0].get("content",{}).get("parts",[])
    output="".join(p.get("text","") for p in parts if isinstance(p,dict))
    if not output.strip():
        raise RuntimeError(f"Gemini returned no text: {json.dumps(data)[:1500]}")
    return output

def model_generate(pages, opportunities, feedback=""):
    compact=pages[-240:]
    opps=sorted(opportunities,key=lambda x:x.get("priority",0),reverse=True)[:12]
    prompt=f"""
You are the senior SEO editor for Xenors.in. Your job is NOT to fill a publishing quota. Your job is to choose ONE article only when it has a credible path to organic traffic and strengthens Xenors topical authority.

BUSINESS GOAL
- Build toward 100k-250k organic monthly pageviews in six months.
- Quality, search demand, topical authority and click potential outrank article count.
- If no strong opportunity exists, return a SKIP decision instead of filler.

EDITORIAL AUTHORITY
{chr(10).join("- "+x for x in PRIORITIES)}

CURRENT GSC-BACKED OPPORTUNITIES
{json.dumps(opps, ensure_ascii=False)}

EXISTING XENORS PAGES
{json.dumps(compact, ensure_ascii=False)}

{("EDITORIAL FEEDBACK FROM A REJECTED DRAFT:\n"+feedback) if feedback else ""}

Choose a topic that is adjacent to a proven opportunity, but has a clearly different primary intent from the existing page. Prefer implementation, troubleshooting, commissioning, comparison, architecture, test plans, failure analysis, calculations, buyer decision criteria or real engineering workflows.

Hard rules:
- Never invent a topic merely to satisfy a slot.
- Do not duplicate or cannibalize an existing page.
- The chosen topic must cite a specific opportunity_id from the GSC opportunity map unless XENORS_TOPIC_HINT is provided.
- If the best GSC item is marked new_article_allowed=false, do not build a new article around it.
- Focus on practical engineering value and first-hand-style implementation detail, not generic AI prose.
- Prefer angles that answer a narrow buyer/engineer question better than a broad overview.
- No keyword stuffing, fake urgency, fabricated statistics, invented standards, fake benchmarks, fake quotes, made-up product claims, or unsupported prices.
- Article body target: 2000-3200 words.
- Use clean HTML fragments only in body_html: h2/h3/p/ul/ol/table/pre/code/blockquote.
- Include at least 6 substantive h2 sections.
- Include at least one practical table/checklist/test matrix where useful.
- Include 3-6 real official/canonical source URLs you are highly confident exist.
- Pick 2-4 genuinely relevant internal-link targets by exact existing path.
- section must be one of: {", ".join(sorted(ALLOWED_SECTIONS))}
- slug must be lowercase kebab-case.
- Avoid lazy titles such as generic "Ultimate Guide", "Everything You Need to Know", or near-duplicate "Explained" pages unless the query truly demands it.

If there is no credible traffic opportunity, return:
{{"decision":"skip","reason":"..."}}

Otherwise return ONLY valid JSON:
{{
  "decision":"publish",
  "opportunity_id":"...",
  "section":"ai",
  "slug":"example-slug",
  "title":"...",
  "meta_description":"...",
  "primary_intent":"...",
  "keyword_cluster":["..."],
  "search_gap":"What the current SERP/existing page does not fully answer",
  "why_this_can_win":"Concrete reason this article deserves to exist",
  "hero_subtitle":"...",
  "body_html":"<h2>...</h2>...",
  "internal_link_targets":["ai/example/index.html"],
  "source_urls":["https://..."]
}}
"""
    api_key=os.environ["GEMINI_API_KEY"]
    models=[]
    for m in [MODEL, "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-flash-lite"]:
        if m and m not in models:
            models.append(m)

    last_error=None
    for model_name in models:
        for attempt in range(1,4):
            try:
                output=gemini_request(prompt,model_name,api_key,temperature=0.25)
                print(f"Gemini generation succeeded with {model_name} on attempt {attempt}")
                try:
                    return parse_json(output)
                except json.JSONDecodeError:
                    repair_prompt=f"""Repair the following into STRICT valid JSON only. Preserve meaning and HTML. No markdown fences.

{output}
"""
                    repaired=gemini_request(repair_prompt,model_name,api_key,temperature=0.0)
                    return parse_json(repaired)
            except urllib.error.HTTPError as e:
                body=e.read().decode("utf-8",errors="replace")
                last_error=RuntimeError(f"Gemini API HTTP {e.code} on {model_name}: {body}")
                if e.code in {429,500,502,503,504} and attempt < 3:
                    time.sleep(10 * attempt)
                    continue
                if e.code in {429,500,502,503,504}:
                    break
                raise last_error from e
            except (urllib.error.URLError, TimeoutError) as e:
                last_error=RuntimeError(f"Gemini network error on {model_name}: {e}")
                if attempt < 3:
                    time.sleep(10 * attempt)
                    continue
                break
            except json.JSONDecodeError as e:
                last_error=RuntimeError(f"Gemini returned malformed JSON on {model_name}: {e}")
                break
    raise last_error or RuntimeError("Gemini generation failed after retries and fallback")

def editorial_gate(a, pages, opportunities):
    if a.get("decision")=="skip":
        return {"approved":False,"score":0,"reason":a.get("reason","Model chose to skip weak opportunity"),"feedback":""}

    opp_ids={x.get("id") for x in opportunities}
    if not TOPIC_HINT and a.get("opportunity_id") not in opp_ids:
        return {"approved":False,"score":0,"reason":"Draft is not tied to an approved GSC opportunity.","feedback":"Choose a real opportunity_id from the supplied map."}

    body=BeautifulSoup(a.get("body_html",""),"html.parser")
    words=article_word_count(a)
    h2_count=len(body.find_all("h2"))
    sources=[u for u in a.get("source_urls",[]) if isinstance(u,str) and u.startswith("https://")]
    practical=bool(body.find("table") or body.find("ol") or body.find("pre"))
    sim=too_similar(a.get("title",""),pages)

    hard_fail=[]
    if words < 1800: hard_fail.append(f"too thin: {words} words")
    if h2_count < 6: hard_fail.append(f"only {h2_count} h2 sections")
    if len(sources) < 3: hard_fail.append("fewer than 3 credible source URLs")
    if not practical: hard_fail.append("no practical table/checklist/code/test structure")
    if sim: hard_fail.append(f"title/intent too similar to existing page: {sim}")
    if not a.get("search_gap"): hard_fail.append("missing explicit search gap")
    if not a.get("why_this_can_win"): hard_fail.append("missing reason the article can win")

    if hard_fail:
        return {"approved":False,"score":40,"reason":"; ".join(hard_fail),"feedback":"Fix every hard-fail item and make the article materially more specific and useful."}

    prompt=f"""
Act as a ruthless SEO editor. Score this proposed Xenors article against the business goal of building toward 100k-250k monthly organic pageviews.

Score 0-100 using:
- Search opportunity / demand evidence: 25
- Topical authority fit for Xenors: 20
- Unique search intent / cannibalization safety: 20
- Practical depth and information gain: 20
- Click-worthiness of title/meta: 10
- Evidence/source quality: 5

Reject generic filler even if grammatically good. A passing article needs >=85 overall, and none of the first four categories may score below 15.

GSC opportunities:
{json.dumps(opportunities,ensure_ascii=False)}

Existing page titles:
{json.dumps([p.get("title") for p in pages[-240:]],ensure_ascii=False)}

Candidate:
{json.dumps({k:a.get(k) for k in ["opportunity_id","title","meta_description","primary_intent","keyword_cluster","search_gap","why_this_can_win","source_urls"]},ensure_ascii=False)}

Article text:
{body.get_text(" ",strip=True)[:18000]}

Return ONLY valid JSON:
{{"score":0,"search_opportunity":0,"authority_fit":0,"intent_uniqueness":0,"practical_depth":0,"click_worthiness":0,"evidence":0,"approved":false,"reason":"...","feedback":"specific fixes"}}
"""
    api_key=os.environ["GEMINI_API_KEY"]
    output=gemini_request(prompt,MODEL,api_key,temperature=0.0)
    result=parse_json(output)
    score=int(result.get("score",0))
    key_scores=[int(result.get(k,0)) for k in ["search_opportunity","authority_fit","intent_uniqueness","practical_depth"]]
    result["approved"]=bool(score>=85 and all(x>=15 for x in key_scores) and result.get("approved",False))
    return result

def article_word_count(a):
    return len(re.findall(r"\b[\w'-]+\b", BeautifulSoup(a.get("body_html",""),"html.parser").get_text(" ")))

def expand_article_if_needed(a, min_words=1800):
    if article_word_count(a) >= min_words:
        return a

    api_key=os.environ["GEMINI_API_KEY"]
    expand_prompt=f"""Expand the following Xenors article body so the final article is at least 2200 words while preserving the same title, topic, intent, structure, and factual caution.

Rules:
- Return ONLY valid JSON with one key: body_html
- Keep existing useful sections and add practical depth, implementation detail, troubleshooting, checklists, examples, and decision criteria
- Do not invent statistics, standards, prices, release dates, benchmarks, quotes, or product capabilities
- Keep clean HTML fragments only: h2/h3/p/ul/ol/table/pre/code/blockquote
- Do not add html/head/body tags

TITLE:
{a.get("title","")}

CURRENT BODY:
{a.get("body_html","")}
"""
    models=[]
    for m in [MODEL, "gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-3.1-flash-lite"]:
        if m and m not in models:
            models.append(m)

    last_error=None
    for model_name in models:
        for attempt in range(1,4):
            try:
                output=gemini_request(expand_prompt,model_name,api_key,temperature=0.25)
                data=parse_json(output)
                body=data.get("body_html","")
                if body:
                    a["body_html"]=body
                    if article_word_count(a) >= min_words:
                        print(f"Expanded thin article with {model_name} on attempt {attempt}")
                        return a
                    last_error=RuntimeError(f"Expanded article still below {min_words} words")
            except urllib.error.HTTPError as e:
                body=e.read().decode("utf-8",errors="replace")
                last_error=RuntimeError(f"Gemini expansion HTTP {e.code} on {model_name}: {body}")
                if e.code in {429,500,502,503,504} and attempt < 3:
                    time.sleep(10 * attempt)
                    continue
                if e.code in {429,500,502,503,504}:
                    break
                raise last_error from e
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as e:
                last_error=RuntimeError(f"Gemini expansion failed on {model_name}: {e}")
                break

    raise last_error or RuntimeError("Unable to expand thin article")

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

def update_source_date(rel_path):
    p = ROOT / "config" / "source_dates.json"
    data = {}
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
    data[rel_path] = NOW.date().isoformat()
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

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

def trim_text(value, max_len):
    value=re.sub(r"\s+"," ",str(value or "")).strip()
    if len(value)<=max_len:
        return value
    cut=value[:max_len+1]
    if " " in cut:
        cut=cut.rsplit(" ",1)[0]
    return cut.rstrip(" .,:;|-")

def normalize_article(a):
    a["title"]=trim_text(a.get("title",""),85)
    a["meta_description"]=trim_text(a.get("meta_description",""),175)

    if len(a["title"])<30:
        intent=trim_text(a.get("primary_intent",""),42)
        if intent:
            candidate=f"{a['title']}: {intent}".strip(": ")
            a["title"]=trim_text(candidate,85)

    if len(a["meta_description"])<110:
        extra=trim_text(a.get("hero_subtitle",""),90)
        if extra:
            combined=(a["meta_description"].rstrip(". ") + ". " + extra).strip()
            a["meta_description"]=trim_text(combined,175)

    return a

def validate(a,pages):
    if a.get("section") not in ALLOWED_SECTIONS:
        raise ValueError("Invalid section")
    if not slug_ok(a.get("slug")):
        raise ValueError("Invalid slug")
    if len(a.get("title",""))<30 or len(a.get("title",""))>85:
        raise ValueError("Title length outside safe range")
    if len(a.get("meta_description",""))<110 or len(a.get("meta_description",""))>175:
        raise ValueError("Meta description length outside safe range")
    if article_word_count(a)<1800:
        raise ValueError("Article too thin after automatic expansion")
    body=BeautifulSoup(a.get("body_html",""),"html.parser")
    if len(body.find_all("h2"))<6:
        raise ValueError("Article lacks enough substantive sections")
    sources=[u for u in a.get("source_urls",[]) if isinstance(u,str) and u.startswith("https://")]
    if len(sources)<3:
        raise ValueError("Article lacks enough credible source URLs")
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
        print(f"Slot {slot} already published: {state.get('last_url')}")
        return
    pages=existing_pages()
    opportunities=load_opportunities()
    article=model_generate(pages,opportunities)
    if article.get("decision")=="skip":
        print(f"EDITORIAL SKIP: {article.get('reason','No strong opportunity')}")
        return

    article=normalize_article(article)
    article=expand_article_if_needed(article,1800)
    gate=editorial_gate(article,pages,opportunities)

    if not gate.get("approved"):
        print(f"First draft rejected by editorial gate: score={gate.get('score')} reason={gate.get('reason')}")
        article=model_generate(pages,opportunities,feedback=gate.get("feedback") or gate.get("reason",""))
        if article.get("decision")=="skip":
            print(f"EDITORIAL SKIP AFTER REVISION: {article.get('reason','No strong opportunity')}")
            return
        article=normalize_article(article)
        article=expand_article_if_needed(article,1800)
        gate=editorial_gate(article,pages,opportunities)

    if not gate.get("approved"):
        print(f"EDITORIAL SKIP: final score={gate.get('score')} reason={gate.get('reason')}")
        return

    print(f"Editorial gate approved score={gate.get('score')}: {gate.get('reason','')}")
    validate(article,pages)
    hero_name=f"{article['slug']}-hero.webp"
    hero_path=ROOT/"images"/hero_name
    make_hero(article["title"],article["hero_subtitle"],hero_path)
    out=ROOT/article["section"]/article["slug"]/"index.html"
    out.parent.mkdir(parents=True,exist_ok=False)
    out.write_text(render_page(article,hero_name),encoding="utf-8")
    update_source_date(out.relative_to(ROOT).as_posix())
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

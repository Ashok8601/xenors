# ARTICLE_CHANGES.md

## Page
- URL: https://xenors.in/ai/how-to-make-ai-videos-for-free/
- Source: `ai/how-to-make-ai-videos-for-free/index.html`
- Published / modified: 2026-11-07
- Approx. article word count before build shell: 2,500 words

## Content changes
- Rebuilt the article as one end-to-end six-step workflow: Idea -> Script -> Scenes -> Generate -> Voice/Captions -> Edit/Export.
- Added an ~80-word quick answer naming ChatGPT + Google Flow/Adobe Firefly + Clipchamp as a practical stack.
- Added a six-tool comparison table: Google Flow, Adobe Firefly, Runway, Pika, Canva AI/Video Editor, Microsoft Clipchamp.
- Added only plan facts supported by current official documentation; uncertain fields explicitly say to check the current official page.
- Completed the Mars example through Scene 6 with closing CTA.
- Merged platform-specific thin sections into one export-settings table for YouTube, Shorts and Instagram.
- Expanded Hindi/Hinglish workflow with three practical prompts and caption guidance.
- Added a no-watermark section with tool-specific caveats and a warning about untrusted watermark-removal sites.
- Added common-problem fixes for face drift, hands, flicker, lip sync, boring pacing and credit waste.
- Added a visible author/byline, published date, last-updated date and a transparent "How this guide was tested and verified" section.
- Added ethics/copyright guidance and YouTube AI-disclosure guidance.
- Added a Sources section linking to official product/help pages.

## Visuals
- Added an original non-screenshot workflow hero: `images/how-to-make-ai-videos-for-free-hero.webp`.
- Hero size: 8,324 bytes, 1200x630, WebP, fetchpriority=high, explicit width/height.
- Added two explicit `<!-- IMAGE: ... -->` slots for the site owner to replace with real screenshots later; no fake screenshots were created.
- Added a final-result video embed placeholder that clearly says to use a real finished video.

## SEO / schema
- Title: `How to Make AI Videos for Free (2026): Step-by-Step` (51 chars).
- Meta description: 138 chars.
- Self-canonical: `https://xenors.in/ai/how-to-make-ai-videos-for-free/`.
- Added BlogPosting schema with Person author, datePublished, dateModified and image.
- Added BreadcrumbList schema.
- Added Open Graph image/title/description and Twitter card/title/description/image.
- No fabricated FAQ rich-result claims were added.

## Site integration
- Uses the existing Xenors global CSS pipeline (`styles/seo-global.css` -> generated `/assets/xenors-core.css`); no standalone article CSS is required.
- Build pipeline injects the existing site header, footer, consent banner, follow box and related/cluster links.
- Added contextual inbound links from:
  - `/ai/`
  - `/ai/how-to-build-an-ai-agent-with-chatgpt/`
  - `/ai/ai-tools-in-2027-100-top-picks/`
  - `/ai/google-gemini-agent-for-work-2026/`
- The article links back to the AI hub, AI tools article and ChatGPT workflow guide.
- Added source date to `config/source_dates.json` so sitemap/feed use the real page date.
- Build automatically added the article to `sitemap.xml`, `feed.xml` and `latest.json`.

## Build verification
Command run: `python build.py`

Result:
- HTML pages: 446
- Sitemap URLs: 443
- Redirects: 201
- Validator errors: 0
- Validator warnings: 0
- Build exit: 0
- New URL present in sitemap: YES
- New URL present in feed: YES
- New URL present in latest.json: YES
- Consent banner markup in built article: YES
- Follow markup in built article: YES

## Lighthouse mobile
NOT VERIFIED. Chromium is available in the build environment, but Lighthouse CLI is not installed. No Lighthouse score has been invented.

## Official sources checked on 2026-11-07
- Google Flow credits: https://support.google.com/flow/answer/16526234
- Google Flow watermark/help: https://support.google.com/flow/answer/16353333
- Adobe Firefly plans: https://www.adobe.com/products/firefly/plans.html
- Adobe Firefly AI video: https://www.adobe.com/products/firefly/features/ai-video-generator.html
- Runway credits: https://help.runwayml.com/hc/en-us/articles/15124877443219-How-do-credits-work
- Runway usage rights: https://help.runwayml.com/hc/en-us/articles/18927776141715-Usage-rights
- Pika FAQ: https://pika.art/faq
- Canva video clip help: https://www.canva.com/help/video-clip/
- Canva pricing/help: https://www.canva.com/pricing/
- Clipchamp plans: https://support.microsoft.com/en-us/clipchamp/what-are-the-clipchamp-paid-plans-and-how-do-they-work
- YouTube AI disclosure: https://support.google.com/youtube/answer/14328491

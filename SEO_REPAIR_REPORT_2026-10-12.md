# Xenors SEO Repair Report — 12 October 2026

## Static validation after repairs
- HTML pages checked: **223**
- Indexable pages: **220**
- Sitemap URLs: **220**
- Broken internal links: **0**
- Internal links pointing to redirect sources: **0**
- Missing local image/script assets: **0**
- Title-length diagnostics outside the target range: **0**
- Meta-description length diagnostics outside the target range: **0**
- H1 issues on normal indexable pages: **0**
- Indexable canonical URLs missing from sitemap: **0**
- Historical GSC 404 URLs supplied: **47**
- Historical GSC 404 URLs without a current page/rewrite/redirect: **0**

## Code Lab
- Code Lab HTML pages: **118**
- Pages under 1,000 visible content words: **0**
- Minimum visible content words: **1016**
- Median visible content words: **1346**
- Code Lab header/footer are separate from the normal Xenors shell.
- Build-only `_shared` header/footer files use `.inc`, not `.html`, so crawlers do not treat them as title-less pages.
- Code Lab pages no longer link the breadcrumb Home item to a missing `/home/` URL.
- `/home/` now has a real, useful Learning Hub page.

## Fixes tied to the supplied audit screenshots
### Ahrefs: 105 pages linking to a broken page
The Code Lab breadcrumb previously pointed to `/home/` while no `/home/index.html` existed. The package now provides a real `/home/` page and uses clean breadcrumb/internal-link targets. Static validation finds **0 broken internal links**.

### Ahrefs: 404 / 4XX
The 47 historical GSC 404 URLs were reviewed. Every supplied URL now resolves through a current page, a 200 rewrite where appropriate, or a permanent redirect for an obsolete/case-variant URL. See `GSC_LEGACY_URL_FIX_MAP.csv`.

### Ahrefs: title, description and H1 warnings
Titles and descriptions were normalized across indexable pages. The Gemini Web Story now has visible story text and an H1. The accidental duplicate nested Gemini story was removed.

### Ahrefs: blocked resources
`robots.txt` no longer blocks `/components/` or the Code Lab `_shared` directory, because those locations contain CSS/JS required to render pages. Build-only fragments are kept out of the sitemap instead of blocking important resources.

### Missing Web Story assets
The US Stocks Web Story referenced nine nonexistent `/Web-Stories/images/...` files. New local WebP story images were created and all AMP image URLs were updated. Static validation now reports **0 missing local assets**.

### Ubersuggest: two pages with no title
The Code Lab header/footer partials used to be `.html` files and were picked up by the sitemap/build scan. They are now `.inc` files and `_shared` files are excluded from the public-page build/sitemap pipeline.

### Ubersuggest: short/long titles and descriptions
Code Lab page titles were rewritten into descriptive tutorial titles and all current indexable pages pass the package's title/meta-description diagnostics.

## GSC exclusions
A `noindex` status is not automatically an error. Login/signup pages should remain non-indexable. Privacy/Terms pages are now handled as normal public pages by the build. Historical reports can remain visible until Google recrawls them.

“Crawled - currently not indexed” cannot be forced from code. The supplied AI-agent pages are in the sitemap and have stronger internal linking from the AI hub and related-reading system. Google still decides whether and when to index them.

## 3XX note
The package has **0 internal links pointing to redirect sources**. Permanent redirects are intentionally retained for obsolete uppercase, `.html`, typo and legacy URLs because removing those redirects would turn old external/history URLs back into 404s. A crawler that deliberately tests old URLs may still report those URLs as redirects; that is correct HTTP behavior, not a broken internal-link problem.

## Ranking / traffic note
A clean technical audit improves crawlability and removes avoidable errors, but it cannot guarantee a 99/100 score in every third-party crawler, Google indexing, 1,000 monthly visits, or rankings above W3Schools/GeeksforGeeks. Their authority, age, backlinks and brand demand cannot be reproduced by a ZIP. The included Code Lab keyword plan is designed to grow through focused tutorial and long-tail queries first.

# Xenors.in — Root Deployable Static Website

This package is ready for a normal static host. `index.html` is intentionally at the ZIP/project root.

## Important files
- `index.html` — homepage served at `/`
- `404.html` — custom not-found page
- `robots.txt` — crawler rules
- `sitemap.xml` — canonical URLs for search engines
- `_redirects` — legacy redirect map for hosts that support this format
- `render.yaml` — Render configuration; publish directory is `.`
- `config/redirects.csv` — readable old URL -> new URL migration map
- `docs/REDIRECT_MAP.md` — documented migration list

## Page structure
Each canonical URL has its own folder and `index.html`.
Example:

`/finance/investing/` -> `finance/investing/index.html`

`/ai/tools/` -> `ai/tools/index.html`

This keeps the site easy to maintain while preserving clean public URLs.

## Render
Use the included `render.yaml`, or set manually:
- Build Command: `echo "Static site ready"`
- Publish Directory: `.`

Do not delete the redirect rules while old URLs remain indexed in Google.

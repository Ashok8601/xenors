# Structure & SEO Notes

## Why this structure is cleaner

1. **One canonical HTML file per indexable URL.** Duplicate `.html`, uppercase-folder and legacy copies are removed from the editable source.
2. **Legacy URLs are configuration, not duplicate pages.** Old indexed URLs are preserved through permanent 301 redirects.
3. **Internal links are normalized.** Where an old URL matched the redirect map, links in canonical pages now point directly to the final URL instead of taking a redirect hop.
4. **Sitemap is generated from one page inventory.** `config/pages.json` is the source of truth, preventing duplicate/legacy URLs from leaking into `sitemap.xml`.
5. **Canonical tags are preserved.** Each page points to its final `https://xenors.in/.../` URL.
6. **Custom 404 is retained.** Unknown URLs should return the host's 404 response and show `404.html`; they should not be rewritten to the home page.
7. **Easy maintenance.** URL folder = source page folder, redirect map is a single CSV, build logic is in one script.

## SEO-safe workflow for future URL changes

- Prefer keeping an existing indexed URL unchanged.
- If a URL must change, add exactly one `old_url,new_url,301` row to `config/redirects.csv` and the equivalent route to `render.yaml`.
- Point internal links and canonical tags directly to the new URL.
- Put only the final URL in `config/pages.json` / sitemap.
- Avoid redirect chains and redirect loops.
- Do not create both old and new pages with the same content.

## Before every deploy

```bash
python scripts/build.py
python scripts/check_site.py
```

Then deploy `dist/` through Render.

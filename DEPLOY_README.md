# Xenors — Render Production Deployment

This package is intended for a **Render Static Site**.

## Render settings

```text
Build Command: pip install -r requirements.txt && python build.py && python validate_site.py
Publish Directory: .
```

`render.yaml` already contains these settings.

## What happens during build

1. Python dependencies are installed.
2. `build.py` injects the shared Xenors header/footer/read-also, shared CSS/JS, analytics and configured ad scripts in their intended document locations.
3. `build.py` refreshes sitemap/output metadata and removes stale generated markup.
4. `validate_site.py` audits the generated static site.
5. Render publishes only if validation succeeds.

## After deployment

Check:

- `/`
- `/ai/`
- `/plc/`
- `/sitemap.xml`
- `/robots.txt`
- one Tech article
- one AI article
- one Finance article
- mobile hamburger navigation

Then submit/resubmit `https://xenors.in/sitemap.xml` in Google Search Console and monitor indexing/impressions.

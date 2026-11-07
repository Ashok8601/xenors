# Xenors SEO + Engagement Audit — 2026-11-07

## GSC baseline from uploaded export
- Clicks: 48
- Impressions: 6850
- CTR: 0.70%
- Impression-weighted average position: 36.54
- Export window: last 3 months (22 daily rows present in chart sheet)

## Critical fixes applied
- Rebuilt a valid XML sitemap from indexable canonical pages. The supplied sitemap contained a second XML declaration inside the URL set.
- Normalized double-slash canonicals across affected AI/Tech/PLC pages.
- Public editorial pages now consistently use index/follow directives. Login, signup and 404 remain intentionally noindex because indexing utility/error pages is harmful rather than beneficial.
- Removed three intrusive third-party ad-network script injections from generated pages and disabled future injection in build.py.
- Added lightweight reading-progress and automatic on-page navigation for long articles.
- Added scroll-depth GA4 events (50% and 90%) without faking engagement time.
- Improved snippets for high-impression / low-CTR pages found in the GSC export.
- Added a dedicated `/share-market/can-trading-make-you-a-billionaire/` page because that URL had 305 impressions at average position 6.9 in the uploaded GSC data but was absent from the ZIP.
- Added canonical redirect rules for major slash/no-slash variants.
- Improved duplicate meta descriptions and missing image alt/lazy-loading attributes.

## Final static audit
- HTML files scanned: 443
- Indexable sitemap URLs: 440
- Editorial noindex pages: 0
- Missing editorial canonical: 0
- Double-slash canonical: 0
- Duplicate canonical groups: 0
- Duplicate description groups: 0
- Editorial pages with H1 count != 1: 0

## Highest GSC opportunities (impressions >=20, average position <=20)
- https://xenors.in/share-market/can-trading-make-you-a-billionaire/ — 305 impressions, 0 clicks, CTR 0.00%, position 6.90
- https://xenors.in/share-market/how-to-earn-1000-rupees-per-day-from-trading/ — 261 impressions, 0 clicks, CTR 0.00%, position 15.09
- https://xenors.in/ai/google-gemini-agent-for-work-2026 — 173 impressions, 0 clicks, CTR 0.00%, position 7.04
- https://xenors.in/share-market/invest-10-and-earn-daily/ — 164 impressions, 5 clicks, CTR 3.05%, position 8.86
- https://xenors.in/ai/ai-pedestrian-detection-system/ — 122 impressions, 7 clicks, CTR 5.74%, position 11.36
- https://xenors.in/share-market/how-to-earn-1000-rupees-per-day-from-trading — 110 impressions, 0 clicks, CTR 0.00%, position 8.97
- https://xenors.in/share-market/how-to-earn-20000-per-day-in-stock-market — 78 impressions, 4 clicks, CTR 5.13%, position 5.37
- https://xenors.in/home/code-lab/html/html-section-article-aside/ — 76 impressions, 2 clicks, CTR 2.63%, position 11.83
- https://xenors.in/ai/openai-dots/ — 66 impressions, 1 clicks, CTR 1.52%, position 12.76
- https://xenors.in/ai/how-to-build-an-ai-agent-with-chatgpt/ — 58 impressions, 3 clicks, CTR 5.17%, position 5.83
- https://xenors.in/ai/gpt-6-1-sol-ultrafast-explained — 55 impressions, 0 clicks, CTR 0.00%, position 11.56
- https://xenors.in/share-market/how-to-earn-3000-per-day-in-stock-market — 54 impressions, 2 clicks, CTR 3.70%, position 8.13
- https://xenors.in/ai/google-search-agents-seo-website-traffic-2026 — 53 impressions, 0 clicks, CTR 0.00%, position 11.00
- https://xenors.in/share-market/can-trading-make-you-a-millionaire-in-india — 52 impressions, 0 clicks, CTR 0.00%, position 14.27
- https://xenors.in/data-science/transfer-learning-keras-pytorch/ — 51 impressions, 1 clicks, CTR 1.96%, position 15.80
- https://xenors.in/share-market/how-to-earn-3000-per-day-in-stock-market/ — 47 impressions, 0 clicks, CTR 0.00%, position 5.94
- https://xenors.in/share-market/how-much-money-can-you-make-from-stocks-in-a-month/ — 42 impressions, 0 clicks, CTR 0.00%, position 15.43
- https://xenors.in/ai/ — 41 impressions, 0 clicks, CTR 0.00%, position 5.71
- https://xenors.in/ai/ai-tools-in-2027-100-top-picks/ — 41 impressions, 0 clicks, CTR 0.00%, position 16.80
- https://xenors.in/data-science/pyspark-tutorial-data-science/ — 39 impressions, 0 clicks, CTR 0.00%, position 15.97

## CTR expectation
A site-wide 30% organic CTR cannot be guaranteed and would be unrealistic at an average position around 36.5. The practical path is to move more high-impression queries into positions 1–3 and improve snippets for pages already ranking in the top 10–15.

## Engagement note
The GA4 screenshot showed a very large Singapore share compared with India/US and only ~4 seconds average engagement. Combined with the third-party ad-network scripts found in the source, this can indicate low-quality/ad-network traffic mixed with real readers. Removing intrusive scripts should improve traffic quality and page experience; it may reduce raw active-user counts while improving meaningful engagement.

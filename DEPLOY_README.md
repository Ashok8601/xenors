# Xenors deployment and publishing guide

## 1. Build locally

From the project root:

```bash
python -m pip install -r requirements.txt
python build.py
```

Success means the command exits `0` and the validator prints `errors: 0` and `warnings: 0`.

**Deploy only `dist/` as the public website.** The project root contains source pages, component templates, build scripts and reports that should not be public.

## 2. Redirect source of truth

Edit only:

```text
config/redirects.csv
```

Columns:

```text
old,new,status
```

Run `python build.py`. It regenerates:

- `_redirects` for hosts that support Netlify/Cloudflare Pages style redirect files.
- `render.yaml` routes for Render.

Do not hand-edit both redirect outputs independently.

## 3. Render settings

The generated `render.yaml` is configured for:

- Runtime: Static
- Build command: `pip install -r requirements.txt && python build.py`
- Publish directory: `./dist`

Render reads `render.yaml`. The `_redirects` file is also placed inside `dist/` for hosts that use that convention; it is not the redirect source of truth.

## 4. Add a new post

Create a real static file:

```text
<section>/<slug>/index.html
```

Do not create routes in JavaScript.

Add real article content with one H1 and a useful title/description. Then add the article's actual source revision date to `config/source_dates.json` if the file is not tracked in Git yet.

Run one command:

```bash
python build.py
```

The build will generate canonical metadata, sitemap, Atom feed, `latest.json`, redirects and `dist/`, then validate everything.

## 5. Cookie consent behavior

The banner is implemented by:

- `/components/consent-subscribe.js`
- `/components/consent-subscribe.css`

Default Consent Mode v2 values are denied for:

- `ad_storage`
- `analytics_storage`
- `ad_user_data`
- `ad_personalization`

GA4 is loaded only when analytics consent is granted. The choice is stored in localStorage. “Cookie settings” in the footer reopens the controls.

## 6. OneSignal web push setup

The project already contains `OneSignalSDKWorker.js` at the site root and delayed initialization after consent.

In OneSignal:

1. Create/open the Xenors app.
2. Add **Web Push** as the platform.
3. Choose the custom/typical website setup appropriate for `https://xenors.in`.
4. Copy the public **App ID**.
5. Open `config/public-subscriptions.js` and set:

```js
window.XENORS_SUBSCRIBE_CONFIG={
  oneSignalAppId:'YOUR-PUBLIC-APP-ID',
  emailFormAction:''
};
```

6. Run `python build.py` and deploy `dist/`.
7. Accept site consent, scroll past 50%, click **Enable web push**, and verify the browser permission prompt and a test notification.

As checked on 2026-11-07, OneSignal's official pricing page lists the Free plan with web push up to **10,000 subscribers per send** and API send access. Source: https://onesignal.com/pricing/

A direct current free **RSS-to-push** automation was not verified from official docs. Until you configure an external automation, use this manual send checklist after publishing:

1. Run `python build.py`.
2. Open `dist/latest.json` and confirm the first entry is the new article.
3. Deploy.
4. In OneSignal, create **New Push**.
5. Audience: subscribed users (or a test segment first).
6. Use the new article title, a short factual description, and its canonical URL.
7. Review and send.

Do not put a OneSignal REST API key into website JavaScript. If later automating via CI/Zapier, store the API key in that platform's secret store.

## 7. Email subscription setup

The static site cannot store subscribers itself. Use a hosted form provider that supports double opt-in.

The markup already submits to the public form URL you configure here:

```js
window.XENORS_SUBSCRIBE_CONFIG={
  oneSignalAppId:'...',
  emailFormAction:'YOUR-HOSTED-FORM-ACTION'
};
```

### Buttondown

As checked on 2026-11-07, Buttondown lists the first 100 subscribers as free, while **RSS-to-email support is a +$9/month add-on**. Source: https://buttondown.com/pricing

For automatic RSS-to-email:

1. Create a Buttondown newsletter and enable double opt-in/confirmation as appropriate in the provider settings.
2. Copy its hosted form POST action into `emailFormAction`.
3. If paying for RSS-to-email, use this feed URL: `https://xenors.in/feed.xml`.
4. Test with your own email first.

### MailerLite alternative

MailerLite's current Free plan (checked 2026-11-07) lists up to 250 active subscribers and 2,500 emails/month, but its documentation states **RSS campaigns are a paid feature**. Sources:

- https://www.mailerlite.com/help/free-plan-update-faq
- https://www.mailerlite.com/help/how-to-create-an-rss-campaign

If you stay on a free email plan, use a manual campaign after each post; the generated `feed.xml` and `latest.json` make the newest article easy to copy into the campaign.

## 8. Feed files

Every build creates:

- `https://xenors.in/feed.xml` — Atom, latest 30 posts, absolute URLs.
- `https://xenors.in/latest.json` — latest post metadata for lightweight tooling.

A visible RSS link and `<link rel="alternate" type="application/atom+xml">` are included.

## 9. Search Console after deployment

1. Deploy and verify `https://xenors.in/sitemap.xml` opens as XML.
2. Search Console -> **Sitemaps**.
3. Submit/re-submit `sitemap.xml`.
4. Use **URL Inspection** on the priority URLs below.
5. Confirm the inspected canonical is the same trailing-slash URL.
6. Click **Request indexing** only after the live URL returns 200 and the updated content is visible.

Priority 10 URLs based on the supplied GSC opportunity data and repaired routes:

1. `https://xenors.in/share-market/can-trading-make-you-a-billionaire/`
2. `https://xenors.in/share-market/how-to-earn-1000-rupees-per-day-from-trading/`
3. `https://xenors.in/ai/google-gemini-agent-for-work-2026/`
4. `https://xenors.in/share-market/invest-10-and-earn-daily/`
5. `https://xenors.in/ai/ai-pedestrian-detection-system/`
6. `https://xenors.in/ai/how-to-build-an-ai-agent-with-chatgpt/`
7. `https://xenors.in/ai/gpt-6-1-sol-ultrafast-explained/`
8. `https://xenors.in/ai/google-search-agents-seo-website-traffic-2026/`
9. `https://xenors.in/ai/openai-dots/`
10. `https://xenors.in/ai/ai-tools-in-2027-100-top-picks/`

Request indexing does not guarantee ranking; it is only a crawl/indexing request.

## 10. 404 verification after deployment

The package contains a noindex `404.html`. After deployment, test a nonsense URL such as:

```text
https://xenors.in/this-page-should-not-exist-92841/
```

Verify in browser DevTools/Network or `curl -I` that the response is HTTP 404, not 200. Host-specific custom-404 status behavior is not claimed until this live check is done.

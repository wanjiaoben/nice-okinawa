# Audit Issues

## 2026-07-04: activity sitemap language URLs return 404

- Status: open
- Type: existing production URL/SEO issue
- Affected site: `activity.nice.okinawa`
- Evidence date: 2026-07-04 JST
- Evidence:
  - `https://activity.nice.okinawa/` returns 200.
  - `https://activity.nice.okinawa/zh-TW/` returns 404.
  - `https://activity.nice.okinawa/ja/` returns 404.
  - `https://activity.nice.okinawa/en/` returns 404.
  - `https://activity.nice.okinawa/ko/` returns 404.
  - `https://activity.nice.okinawa/th/` returns 404.
- Local diagnosis:
  - `sitemap.xml` lists directory-style language URLs.
  - Local language pages existed under `mnt/user-data/outputs/{lang}/index.html`, not at site-root `{lang}/index.html`.
- Required follow-up:
  - Move language pages to site-root directory URLs matching sitemap.
  - Recheck canonical and hreflang.
  - Re-run sitemap curl after deployment.

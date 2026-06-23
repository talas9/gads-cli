# gads CLI — External API Knowledge Base

Documentation-sourced reference for every external Google API the `gads` CLI talks to.
Each KB file is built from **official Google docs fetched on 2026-06-23** (not training memory);
every endpoint/version/claim cites a source URL, and anything that couldn't be doc-verified is
marked `(unverified)`.

Machine-readable summary: [`manifest.json`](./manifest.json).

## APIs

| # | API | KB file | Current version | Status / key sunset |
|---|-----|---------|-----------------|----------------------|
| 1 | **Google Ads REST API** | [google-ads.md](./google-ads.md) | v24.1 GA (v24.2 announced); CLI default `v24` | Active. No per-version sunset dates published; versions typically supported ~12 months. **Customer Match offline uploads change April 1 2026** (token must have a prior successful Customer Match request). |
| 2 | **Merchant API** (new) | [merchant-api.md](./merchant-api.md) | v1 GA | Active. v1beta **discontinued 2026-02-28**. Legacy Content API for Shopping **v2.1 sunsets 2026-08-18** — migrate before then. |
| 3 | **GA4 Data + Admin APIs** | [ga4.md](./ga4.md) | Data API v1beta (stable); Admin API v1beta (stable) / v1alpha (preview). CLI uses Data v1beta + Admin v1alpha for key events. | Active. No sunset announced. Admin key events also exist in stable v1beta — CLI could migrate off v1alpha. |
| 4 | **Google Business Profile** (suite) | [gbp.md](./gbp.md) | Account Mgmt v1, Business Information v1, Performance v1 (all active); legacy My Business v4 for Reviews/Posts | Mixed. v1 APIs active. Legacy **v4 Reviews/Posts still active, no sunset announced**; most other v4 resources already sunset. API access requires **allowlist approval** (un-allowlisted projects get HTTP 429 at 0 quota). |
| 5 | **Search Console API** | [search-console.md](./search-console.md) | `webmasters/v3` REST endpoints (active); discovery name now `searchconsole` v1; URL Inspection on `searchconsole.googleapis.com/v1` | Active. The `webmasters` → `searchconsole` rename was discovery-level only; REST URLs unchanged. CLI's `webmasters/v3` base is correct. |

## OAuth scopes at a glance

| API | Scope(s) |
|-----|----------|
| Google Ads | `https://www.googleapis.com/auth/adwords` |
| Merchant API | `https://www.googleapis.com/auth/content` |
| GA4 | `analytics.readonly` (reads); `analytics.edit` (Admin key-event writes) |
| GBP | `https://www.googleapis.com/auth/business.manage` |
| Search Console | `webmasters.readonly` (reads); `webmasters` (writes) |

## Top coverage gaps (feed the next "add support" task)

- **Google Ads:** `uploadClickConversions` / `uploadCallConversions` (ConversionUploadService), conversion adjustment upload, offline job status polling, `GoogleAdsFieldService` (GAQL field compatibility), audience definition service, PMax asset group management.
- **Merchant API:** Reports sub-API (`reports/v1` ProductView / product_performance_view), `productInputs` write path (insert/patch/delete), dataSource fileUploads status, inventories (local + regional).
- **GA4:** `batchRunReports`, `runPivotReport`, `checkCompatibility`, audience exports, `runFunnelReport`, Admin `keyEvents.patch`, custom dimensions/metrics CRUD.
- **GBP:** Local posts CRUD, monthly search-keyword impressions, batch-get reviews, Google-suggested location updates, business attributes. **Flagged for verification:** CLI's `fetchMultiDailyMetrics` call name/method vs documented `fetchMultiDailyMetricsTimeSeries` — see gbp.md.
- **Search Console:** `startRow` pagination (results may be silently truncated at `rowLimit`), `dataState` ("all"/"hourly") not exposed, server-side `dimensionFilterGroups`, URL Inspection API, sitemap management.

## Notes on verification

- **Google Ads sunset-dates table:** the page exists but the dates table content was not extractable from the fetch — marked `(unverified)` in google-ads.md.
- All other version/status claims were confirmed against the cited doc URLs on 2026-06-23.

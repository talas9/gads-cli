# gads-cli

Unified Google platform CLI for Google Ads, Google Business Profile, Google Merchant Center, and GA4. Built for AI agents — all commands support `--json` and `--help`.

## Related skill

When this CLI is used inside the **talas-ads** workspace, a companion Claude Code skill lives at [`../skills/google-ads-management/SKILL.md`](../skills/google-ads-management/SKILL.md) (symlinked into `~/.claude/skills/`). That skill layers Talas-specific operational knowledge on top of the raw CLI: campaign management workflows, mutation safety (snapshot → mutate → log), cross-channel analysis across Ads + GBP + Merchant Center + GA4, and the business rules for Talas ad copy (PARTS ONLY, Tesla-specific language, branch-specific phone numbers QZ3 / IND4 / SJA, landing-page `?branch=` parameter, etc.). This file (`CLAUDE.md`) stays focused on the generic CLI contract; reach for the skill when the caller is operating the Talas account specifically.

## Quick Start

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your dev token (required), customer ID, and OAuth paths

# 2. Generate OAuth token (opens browser for consent)
python generate_token.py

# 3. Verify setup
./gads doctor
```

## Command Taxonomy

| Group | Subcommands | Purpose | Needs dev token? |
|-------|-----------|---------|-----------------|
| `auth` | `status`, `setup`, `login`, `revoke`, `test` | Credential management and diagnostics | No |
| `campaign` | `list`, `status`, `budget`, `perf` | Campaign management and performance | Yes |
| `adgroup` | `list`, `status`, `create` | Ad group management | Yes |
| `ad` | `list`, `status`, `perf` | Ad management and ad-level metrics | Yes |
| `keyword` | `list`, `add`, `remove`, `negative`, `search-terms`, `ideas`★, `forecast`★ | Keyword research and management | Yes |
| `asset` | `list`, `sitelink`, `callout`, `call` | Asset management and extensions (two-step creation) | Yes |
| `conversion` | `list`, `create`, `tag`, `perf`, `upload` | Conversion tracking and offline upload | Yes |
| `audience` | `list`, `create`, `upload`, `job-status` | Customer Match lists and CSV upload | Yes |
| `report` | `geo`, `hourly`, `devices`, `search-terms` | Specialized performance breakdowns | Yes |
| `gbp` | `accounts`, `locations`, `location`, `reviews`, `reply-review`, `delete-reply`, `perf`, `perf-all`, `search-keywords`, `metrics-list`, `ads-perf`, `ads-daily` | Google Business Profile management + performance analytics | No |
| `gsc` | `sites`, `queries`, `pages`, `performance` | Google Search Console — queries, pages, daily performance | No |
| `merchant` | `account`, `status`, `products`, `product-status`, `feeds`, `shipping`, `returns` | Merchant Center product management | No |
| `ga4` | `report`, `realtime`, `metadata`, `key-events` (`list`/`create`/`bulk`/`delete`) | Google Analytics 4 reporting + key-event (conversion) management | No |
| Top-level | `query`, `perf`, `config`, `refresh`, `snapshot`, `log`, `accounts`, `doctor`, `mutate`, `batch-mutate` | GAQL queries, syncing, snapshots, generic mutations | Yes (except `doctor`) |

> ★ Requires Standard Access developer token

## Authentication Requirements by Service

### Google Ads Commands
- **Developer token:** Required (from Google Ads API Center)
- **OAuth scopes:** `adwords` scope
- **Access level:** Explorer for most commands; Standard for Keyword Planner / Forecasting
- **Credentials:** `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`
- **Important:** Without the developer token, ALL Google Ads API commands fail

### Google Business Profile Commands
- **Developer token:** NOT needed
- **OAuth scopes:** `business.manage` scope
- **Credentials:** `GOOGLE_ADS_LOGIN_CUSTOMER_ID` (optional, for account selection)

### Merchant Center Commands
- **Developer token:** NOT needed
- **OAuth scopes:** `content` scope
- **Credentials:** `GOOGLE_MERCHANT_CENTER_ID`

### GA4 Commands
- **Developer token:** NOT needed
- **OAuth scopes:**
  - `analytics.readonly` — for `report`, `realtime`, `metadata`, and `key-events list`
  - `analytics.edit` — required for `key-events create`, `key-events bulk`, `key-events delete` (uses the GA4 Admin API). The project's `tools/generate_token.py` and `gads-cli/generate_token.py` both include this scope already; if you see `403 Forbidden` on write calls, regenerate the token.
- **APIs to enable:** GA4 Data API (`analyticsdata.googleapis.com`) for reporting; GA4 Admin API (`analyticsadmin.googleapis.com`) for key events.
- **Credentials:** `GOOGLE_GA4_PROPERTY_ID`

## Common GAQL Patterns

```bash
# Basic query
./gads query "SELECT campaign.name, campaign.id FROM campaign"

# With metrics
./gads query "SELECT campaign.name, metrics.clicks, metrics.conversions FROM campaign WHERE metrics.clicks > 0"

# Date-based filtering (yesterday only)
./gads query "SELECT campaign.name, metrics.cost_micros FROM campaign WHERE segments.date = '2026-03-27'"

# Filter by campaign type
./gads query "SELECT campaign.name FROM campaign WHERE campaign.advertising_channel_type = 'SEARCH'"

# Order and limit
./gads query "SELECT campaign.name, metrics.clicks FROM campaign ORDER BY metrics.clicks DESC LIMIT 10"

# Ad group criteria (keywords)
./gads query "SELECT campaign.name, ad_group.name, ad_group_criterion.keyword.text FROM ad_group_criterion"

# Smart/Performance Max campaigns
./gads query "SELECT campaign.name FROM campaign WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'"
```

## Key Environment Variables

```bash
# REQUIRED for Google Ads operations
GOOGLE_ADS_DEVELOPER_TOKEN=xxxxxxxxxxxxxxxx      # From API Center
GOOGLE_ADS_CUSTOMER_ID=1234567890                # 10 digits, no dashes

# REQUIRED for specific services (optional overall)
GOOGLE_ADS_LOGIN_CUSTOMER_ID=9999999999          # MCC manager account ID
GOOGLE_MERCHANT_CENTER_ID=12345678               # MC account
GOOGLE_GA4_PROPERTY_ID=271773771                 # GA4 property ID

# Optional configuration
GADS_TIMEZONE=Asia/Dubai                         # Default: UTC
GADS_CURRENCY=AED                                # Default: USD
GADS_API_VERSION=v19                             # Default: v19

# Paths (auto-detected by default)
GADS_CREDENTIALS_PATH=credentials/google-ads-oauth.json
GADS_DB_PATH=data/gads.db
GADS_SNAPSHOTS_DIR=snapshots
```

## Architecture

```
gads-cli/
├── gads                     # Main CLI entry point (thin shim)
├── gads_lib/
│   ├── cli.py              # Click command groups and entry point
│   ├── config.py           # Environment-driven configuration
│   ├── auth.py             # OAuth credential management + refresh
│   ├── ads.py              # Google Ads REST client + GAQL runner
│   ├── gbp.py              # GBP client (4 base URLs: account mgmt, business info, legacy v4, performance)
│   ├── merchant.py         # Merchant Center REST client
│   ├── ga4.py              # GA4 Data API client
│   ├── http.py             # HTTP helpers with auth headers
│   ├── db.py               # SQLite connection manager
│   ├── output.py           # Table/JSON formatting
│   └── timeutil.py         # Timezone-aware time helpers
├── fetch_daily.py          # Cron-friendly daily data fetcher
├── generate_token.py       # Interactive OAuth token generator
├── pyproject.toml          # Package metadata
└── README.md, CLAUDE.md    # Documentation
```

**REST API design:** The CLI uses Google's REST APIs directly (`requests` + `google-auth`), NOT the Python client library. This keeps dependencies minimal and makes debugging straightforward.

## Known Gotchas

### Google Ads API

1. **Developer token is absolutely required** — without it, every Ads API call fails immediately. GBP/MC/GA4 don't need it.

2. **Tilde (~) in resource names for ad group criteria** — resource names use tilde format: `customers/{CID}/adGroupCriteria/{adGroupId}~{criterionId}`. A slash instead of tilde causes 404 errors. Same pattern for campaign criteria.

3. **mutateOperations key in batch operations** — use `{"mutateOperations": [...]}` not `{"operations": [...]}` for cross-resource mutations. Single-resource mutations use `"operations"`.

4. **Sitelink finalUrls placement** — when creating a sitelink asset, `finalUrls` must be at the top level of the create object, NOT nested inside `sitelinkAsset`. Nesting causes silent URL drops.

5. **Customer Match uploads and April 2026 deprecation** — starting April 1, 2026, `OfflineUserDataJobService` uploads fail if your token has never sent a successful Customer Match request. Pre-upload before that date or switch to Data Manager API.

6. **Asset creation is two-step** — create the asset via `assets:mutate`, then link it to the campaign via `campaignAssets:mutate`. Cannot do both in one call.

7. **Keyword special characters** — endpoints like `generateKeywordIdeas` reject keywords with `! @ % , * '` characters. Always sanitize input.

8. **addyInfo with empty names in Customer Match** — sending `{"addressInfo": {"countryCode": "AE"}}` with no valid names is silently dropped. Validate names before including addressInfo.

### GBP

**Four different base URLs:**
- `mybusinessaccountmanagement.googleapis.com` (v1) — accounts, locations
- `mybusinessbusinessinformation.googleapis.com` (v1) — location details, hours, attributes
- `mybusiness.googleapis.com` (v4, legacy) — reviews, media, posts, Q&A
- `businessprofileperformance.googleapis.com` (v1) — directions, calls, impressions, search keywords

Each endpoint must use its correct base URL or requests fail.

**GBP Performance daily metrics:** BUSINESS_DIRECTION_REQUESTS, CALL_CLICKS, WEBSITE_CLICKS, BUSINESS_IMPRESSIONS_DESKTOP_MAPS, BUSINESS_IMPRESSIONS_DESKTOP_SEARCH, BUSINESS_IMPRESSIONS_MOBILE_MAPS, BUSINESS_IMPRESSIONS_MOBILE_SEARCH, BUSINESS_CONVERSATIONS, BUSINESS_BOOKINGS, BUSINESS_FOOD_ORDERS, BUSINESS_FOOD_MENU_CLICKS.

**GBP Performance reporting lag:** Data takes 2-3 days to populate. Recent days may show zero.

### GSC (Search Console)

- Base URL: `www.googleapis.com/webmasters/v3`
- Requires `webmasters.readonly` OAuth scope (added in v3.3.0)
- Data lags ~3 days (GSC default processing delay)
- Site URL must match verified property exactly (URL-prefix or domain property)

### Database

- **Append-only:** SQLite tables for campaigns, ad groups, keywords, and performance metrics are append-only. No deletions. Use `gads refresh` to pull fresh data; old rows stay.
- **Schema:** Run `python -m gads_lib.db init` to create tables if missing.

### Time and Currency

- **No same-day data:** Google Ads has 24-48h attribution lag. Never analyze today's performance — use yesterday or earlier.
- **All costs in configured currency:** Default is USD. Set `GADS_CURRENCY=AED` if working in AED. All cost_micros from the API are already in that currency.

## CLI Usage Examples

```bash
# Verify setup
./gads doctor
./gads auth status --json

# Query campaigns
./gads query "SELECT campaign.name, campaign.status FROM campaign"
./gads campaign list
./gads campaign list --json

# Performance from local database
./gads perf --days 7
./gads perf --campaign "my-campaign" --json

# Refresh local database from API
./gads refresh --days 3
./gads refresh --days 7 --config --push

# Snapshots (save config before mutations)
./gads snapshot pre-budget-change --save-file
./gads snapshot baseline

# Changelog
./gads log "budget_change" "PMax 25 → 30 AED" --reason "strong cpa"
./gads log "paused_keywords" "15 low-intent keywords" --campaign "Search - Tesla"

# Keyword research (requires Standard access)
./gads keyword ideas --keywords "tesla parts" --language en --geo AE
./gads keyword forecast --keywords "tesla parts" --language en

# Customer Match upload (deprecated April 2026)
./gads audience upload contacts.csv --list-name "Website Visitors" --create-if-missing

# Google Business Profile
./gads gbp accounts
./gads gbp locations --account accounts/123456789
./gads gbp reviews locations/987654321
./gads gbp reply-review accounts/123/locations/456/reviews/789 "Thank you for your review!"
./gads gbp perf -l 17303088970776446827 -d 14
./gads gbp perf-all -d 7 -m "BUSINESS_DIRECTION_REQUESTS,CALL_CLICKS,WEBSITE_CLICKS"
./gads gbp search-keywords -l 17303088970776446827 --months 3
./gads gbp metrics-list

# GBP location asset performance in Google Ads
./gads gbp ads-perf -d 30
./gads gbp ads-daily -d 14

# Google Search Console
./gads gsc sites
./gads gsc queries -s "https://shop.talas.ae/" -d 28
./gads gsc pages -s "https://shop.talas.ae/" -d 28
./gads gsc performance -s "https://shop.talas.ae/" -d 28

# Merchant Center
./gads merchant account
./gads merchant status
./gads merchant products --limit 50

# GA4 reporting
./gads ga4 metadata
./gads ga4 report --dimensions date,country --metrics activeUsers,sessions --start 7daysAgo
./gads ga4 realtime --dimensions city --metrics activeUsers

# GA4 key events (conversions). Write ops need analytics.edit scope.
./gads ga4 key-events list
./gads ga4 key-events create whatsapp_click
./gads ga4 key-events bulk "whatsapp_click,phone_click,form_submit,add_to_cart,begin_checkout,add_payment_info"
./gads ga4 key-events delete whatsapp_click --yes
```

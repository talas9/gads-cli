# Changelog

All notable changes to this project will be documented in this file.

## [3.7.0] - 2026-06-23

### Added
- **GA4 Data API — `batchRunReports`** (`gads ga4 batch-report`): Run up to 5 GA4 reports in a
  single API call, reducing quota overhead. Accepts a `--requests-file` JSON path or uses a
  sensible default (sessions by source + key events by date). Live-verified against property
  271773771.
- **GA4 Data API — `runPivotReport`** (`gads ga4 pivot-report`): Cross-tabulation reports with
  a configurable pivot dimension. Useful for campaign × device or source × medium breakdowns.
- **GA4 Data API — `checkCompatibility`** (`gads ga4 check-compatibility`): Pre-validate which
  dimension+metric combinations are compatible before running a report. Returns 378 dimension
  and 107 metric compatibility entries for the Talas property. Live-verified.
- **GSC — pagination via `startRow`** (`gads gsc queries/pages/performance`): All
  `gsc_search_analytics` calls now support `start_row` offset pagination so queries returning
  exactly `rowLimit` rows are no longer silently truncated.
- **GSC — `dataState` exposure**: All Search Console analytics commands now support `--data-state`
  (`final` / `all` / `hourly_all`) to opt into fresher unconfirmed data.
- **GSC — server-side `dimensionFilterGroups`**: `gsc_search_analytics` now accepts
  `dimension_filter_groups` parameter for server-side filtering before aggregation, avoiding
  rowLimit truncation of large datasets.
- **GSC — URL Inspection API** (`gads gsc inspect URL -s SITE`): Inspect any URL's Google index
  status, indexing state, page fetch state, mobile usability, and last crawl time via the URL
  Inspection API (`searchconsole.googleapis.com/v1`). Read-only. Verified via `--help`; live
  verification pending token regeneration with `webmasters.readonly` scope (see note below).
- **GSC — sitemaps list** (`gads gsc sitemaps -s SITE`): List all submitted sitemaps for a
  Search Console property. Verified via `--help`; live verification pending token regen.
- **GBP — batch-get reviews** (`gads gbp batch-reviews LOCATION_NAME...`): Fetch reviews from
  multiple GBP locations in one command, returning a dict keyed by location name.
- **GBP — local posts list** (`gads gbp local-posts --account A --location L`): List all local
  posts for a GBP location using the legacy v4 API.
- **GBP — local posts create/delete** (`gads gbp create-post` / `gads gbp delete-post`): CRUD
  for GBP local posts. Both commands are WRITE operations — added and verified via `--help` /
  `--dry-run`; NOT live-mutation-verified to avoid mutating the live account.
- **KB drift check** (`gads kb check`): Compares API versions hard-coded in each service module
  against `kb/manifest.json`. Exits non-zero on drift — CI-able. Detected real drift on first
  run: GA4 Admin API uses `v1alpha` in code but `v1beta` is the stable KB-documented version
  (flagged for future migration). `gads kb list` surfaces all KB files with sizes. `gads kb show
  <slug>` prints the full KB doc for any API.
- **KB directory committed**: `gads-cli/kb/` (5 files: google-ads.md, ga4.md, gbp.md,
  search-console.md, merchant-api.md, INDEX.md, manifest.json) is now git-tracked as a shipping
  deliverable.

### Fixed
- **GSC `gsc_search_analytics`**: Added `startRow` and `dataState` fields to the request body
  (previously omitted, causing silent truncation at `rowLimit` and no way to request fresh data).

### Notes
- **GSC live verification pending**: All GSC commands require the `webmasters.readonly` OAuth
  scope. The current token was generated before this scope was added. Re-run `gads auth login
  --force` to regenerate the token and enable live GSC verification.
- **Merchant skipped**: Merchant Center gaps deferred — the `merchantapi.googleapis.com` API is
  not enabled on the GCP project yet. No Merchant changes in this release.
- **GA4 Admin `v1alpha` known drift**: The KB drift check flags GA4 Admin API as DRIFT
  (`v1alpha` in code vs `v1beta` in manifest). Key events still work on `v1alpha`; migrating to
  `v1beta` is a separate task.

## [3.6.0] - 2026-06-23

### Changed
- **Google Ads API default bumped `v19` → `v24`** (`gads_lib/config.py`). v19 was
  sunset 2026-02-11; v24 is the current GA version. GAQL `searchStream`/`search`,
  `mutate`, `uploadClickConversions`, and `generateKeywordIdeas` endpoints are
  unchanged across v23→v24 — version-string-only. Docs (`CLAUDE.md`, `README.md`,
  `.env.example`) updated to state v24.
- **Keyword forecast rebuilt for v24** (`gads_lib/ads.py` `generate_keyword_forecast`).
  v24 reshaped `generateKeywordForecastMetrics`: top-level key is now `campaign`
  (was `campaignToForecast`), keywords moved into `campaign.adGroups[].keywords[]`
  as `{text, matchType}`, `keywordPlanNetwork` removed, `biddingStrategy`
  (manual CPC) is now required, and a forward-looking `forecastPeriod`
  (`startDate`/`endDate`, `YYYY-MM-DD`) is required. The old body returned HTTP 400.

### Fixed
- **`keyword ideas` request payload** (`gads_lib/ads.py` `generate_keyword_ideas`) —
  corrected to the documented `generateKeywordIdeas` REST schema: `language` is a
  single `languageConstants/{id}` string (was the invalid `languageId`),
  `geoTargetConstants` is an array of plain resource-name strings (was objects),
  `keywordPlanNetwork` is now sent, and both-seed requests use `keywordAndUrlSeed`.
  The command previously returned HTTP 400 for all inputs; now returns ideas.
- **`keyword ideas` / `keyword forecast` accept ISO codes** for `--language`
  (`en`, `ar`) and `--geo` (`AE`) in addition to numeric constant IDs, resolved
  to verified `languageConstants`/`geoTargetConstants` IDs (`gads_lib/cli.py`).

### Changed (breaking — Merchant `--json` shape)
- **Merchant Center migrated from Content API for Shopping v2.1 to Merchant API v1**
  (`gads_lib/merchant.py`, host `merchantapi.googleapis.com`). Content API v2.1
  sunsets 2026-08-18. OAuth scope is unchanged (`.../auth/content`). The
  `gads merchant ...` command names and human-readable table columns are preserved,
  but `--json` now returns Merchant API v1 objects, so machine consumers must adapt:
  - `products`: array `resources` → `products`; price `{value,currency}` →
    `productAttributes.price.{amountMicros,currencyCode}` (micros); product id →
    `offerId`; title/availability now under `productAttributes`; `channel` removed.
  - `product-status`: no standalone endpoint in v1 — folded into the products
    resource; statuses read from each product's `productStatus`.
  - `status`: array `accountLevelIssues` → `accountIssues`.
  - `feeds` (data sources): array `resources` → `dataSources`; `name` →
    `displayName`; `fileName` → `fileInput.fileName`; `contentType` → type union.
  - `shipping`: service `name` → `serviceName`; `deliveryCountry` →
    `deliveryCountries[]`; `currency` → `currencyCode`.
  - `returns`: array → `onlineReturnPolicies`.
  All merchant commands remain read-only (GET).

### Security
- **Dependency floors raised** (`pyproject.toml`): `requests>=2.33.0` (closes
  CVE-2024-47081 netrc leak and CVE-2026-25645 temp-file reuse),
  `python-dotenv>=1.2.2` (closes CVE-2026-28684 symlink overwrite),
  `click>=8.1`, `google-auth>=2.35`, `google-auth-oauthlib>=1.2`; dev `pytest>=9.0`,
  `pytest-cov>=6.0` (held below 7.0 which dropped built-in subprocess coverage).

### Notes
- GA4 (Data API v1beta), GBP (Account/Business Info/Performance v1), and GSC
  (webmasters/v3) confirmed current — unchanged. Monitor items: GA4 Admin and
  GBP Reviews still require legacy surfaces (My Business v4 for reviews).

## [3.5.0] - 2026-06-23

### Added
- **`catalog` command** — emits a complete machine-readable manifest of every
  command, subcommand, param, type, default, and help string by walking the live
  Click command tree (`gads catalog --json`). Lets an agent discover the CLI's
  full capabilities without parsing `--help`. Human-readable fallback without
  `--json`. New module `gads_lib/catalog.py`.
- **Structured error envelope + stable exit codes** — `main()` now wraps the CLI
  so failures emit `{"error":{"code":...,"message":...,"exit_code":N}}` to stderr
  when `--json` is in effect (colored text otherwise). Stable codes: 0 OK,
  1 GENERAL, 2 USAGE, 3 AUTH, 4 NOT_FOUND, 5 API, 6 VALIDATION, 7 DB. New
  `print_error()` helper and `EXIT_CODES` in `gads_lib/output.py`.
- **Read-only history-DB access**:
  - `gads db "<SQL>" [--json] [--limit N]` — SELECT-only passthrough to the local
    SQLite history DB. Rejects any mutating/multi-statement SQL (exit code 6) and
    enforces `PRAGMA query_only` as defense in depth.
  - `gads changelog` / `gads decisions` / `gads milestones` `[--json] [-n LIMIT]` —
    native readers for the project's own memory tables.
  - New module `gads_lib/dbread.py` with `assert_select_only`, `run_select`, and
    the convenience readers.
- **`--json` added to `log`, `snapshot`, `refresh`** — these three top-level
  commands now emit structured JSON like every other command.
- **Global `--plain` and `--quiet`/`-q` flags** — `--plain` produces
  deterministic, no-color/no-emoji output for parsing; `--quiet` suppresses
  non-essential progress output.
- **`AGENTS.md` and `llms.txt`** at the CLI root — capability index documenting
  how an agent should drive the CLI (catalog-first discovery, output contract,
  exit codes, reading project memory, mutation discipline).

### Changed
- `cli` root group now carries global `--plain`/`--quiet` options and a context
  object; `main()` runs Click with `standalone_mode=False` to own error handling.

## [3.4.0] - 2026-06-23

### Added
- **`analyze` command group** (5 new read-only analysis commands; no account mutations):
  - `analyze landing-page` — fetches a branch landing page over HTTP and scores it
    (0-100) on message-match, trust signals, mobile/viewport, load weight,
    WhatsApp/branch CTA, and `?branch=` survival; lists concrete issues. Branch
    choices: qz3 / sja / ind4.
  - `analyze wasted-spend` — AED-ranked wasted spend on zero-conversion and
    below-average-CPA search terms and campaigns (window ends yesterday).
  - `analyze ngrams` — 1/2/3-gram clustering of search terms (Arabic + English),
    aggregating cost & conversions per n-gram and surfacing high-cost zero/low-conv
    negative-keyword candidates.
  - `analyze ad-copy` — performance-ranked RSA ads validated against PARTS-ONLY
    business rules (no install/repair/workshop/battery-service; "Tesla" not "EV";
    not OEM/Genuine-only; branch phone). Rules sourced from the `business_rules`
    DB table plus encoded detectors; flags violations by severity.
  - `analyze competition` — competitive pressure from impression-share metrics
    (impression share, top/abs-top IS, rank-lost IS) per keyword, plus a
    best-effort auction-insights attempt that degrades gracefully when the REST
    API does not expose auction-insight fields.
- New `gads_lib/analyze/` sub-package: `lp_score.py`, `wasted_spend.py`,
  `ngrams.py`, `adcopy.py`, `competitive.py`.

### Changed
- Total command groups: 15 → 16 (added `analyze`).

## [3.3.0] - 2026-03-31

### Added
- **GBP Performance API** (4 new commands):
  - `gbp perf` — daily performance metrics for a single location
  - `gbp perf-all` — daily metrics for ALL locations with auto-discovery
  - `gbp search-keywords` — monthly search keyword impressions
  - `gbp metrics-list` — list all available daily metrics
- **GBP Location Asset Performance** (2 new commands, via Google Ads GAQL):
  - `gbp ads-perf` — per-branch aggregate (clicks, impr, CTR, CPC, cost, conv)
  - `gbp ads-daily` — per-branch daily breakdown with totals
  - Uses `asset_set_asset` resource with `LOCATION_SYNC` asset set
  - Matches Ads UI Asset Report > Associations > Location view exactly
- **Google Search Console** (4 new commands, new `gsc` command group):
  - `gsc sites` — list verified Search Console sites
  - `gsc queries` — top search queries with clicks, impressions, CTR, position
  - `gsc pages` — top pages performance
  - `gsc performance` — daily performance time series
- New OAuth scope: `webmasters.readonly` (Search Console access)
- New GCP API: Business Profile Performance API added to `auth setup`
- New GCP API: Search Console API added to `auth setup`
- `auth test` now tests Search Console access
- Scope display in `auth login` now shows Search Console grant status

### Changed
- Total commands: 65 → 75 across 15 groups (was 14)
- GBP commands: 6 → 12
- OAuth SCOPES list: 4 → 5 scopes

## [3.2.0] - 2026-03-28

### Changed
- README: accurate access level documentation (Test/Explorer/Basic/Standard)
- README: Features table now shows all 65 commands across 14 groups
- README: Command Requirements table shows auth needs per command
- CLAUDE.md: AI-agent-friendly reference with full command taxonomy
- CLAUDE.md: GAQL patterns, known gotchas, architecture overview

### Added
- CI pipeline (`.github/workflows/ci.yml`): Python 3.10-3.13 × Ubuntu + macOS
- CI: syntax check, import verification, secret scanning, version validation
- April 2026 Customer Match deprecation warning in docs

## [3.1.0] - 2026-03-27

### Added
- `audience create` — create CRM-based Customer Match user lists
- `audience upload` — full CSV upload pipeline (phone normalization, name validation, SHA-256 hashing, consent, batch retry with 429 backoff)
- `audience job-status` — check Customer Match upload job status and match rate
- `ads.py`: `audience_find_list()`, `audience_create_list()`, `audience_upload_csv()`
- Phone normalization for UAE formats (05X, 5X, 971X, 00971X, +971X)
- Name validation (`is_valid_name`) — rejects companies, garbage, special chars

## [3.0.0] - 2026-03-27

### Added
- **50+ new commands** across 10 new groups
- `campaign list`, `status`, `budget`, `perf` — campaign management
- `adgroup list`, `status`, `create` — ad group management
- `ad list`, `status`, `perf` — ad management with creatives
- `keyword list`, `add`, `remove`, `negative`, `search-terms`, `ideas`, `forecast` — keyword management and research
- `asset list`, `sitelink`, `callout`, `call` — asset management with two-step extension creation
- `conversion list`, `create`, `tag`, `perf`, `upload` — conversion tracking and offline upload
- `audience list` — user list / audience listing
- `report geo`, `hourly`, `devices`, `search-terms` — specialized reports
- `mutate`, `batch-mutate` — generic escape hatches for any API mutation
- `accounts` — list accessible Google Ads accounts
- `ads.py`: `ads_mutate()`, `ads_batch_mutate()`, `ads_search()`, `ads_upload_click_conversions()`, `generate_keyword_ideas()`, `generate_keyword_forecast()`, `sanitize_keyword()`
- Mutation safety: `--dry-run`, `--yes`, auto-changelog logging, caller enforcement

### Changed
- Repo renamed: `google-business-cli` → `gads-cli`
- All internal references updated to `gads-cli`

## [2.2.0] - 2026-03-27

### Added
- Scope-aware configuration: auto-detects project vs global (`~/.config/gads/`)
- `auth setup` wizard detects scope and writes `.env` to correct location
- Currency step in setup wizard
- Developer token access level guide in setup wizard (Test/Basic/Standard + MCC requirement)

### Fixed
- Global pip install now uses `~/.config/gads/` for credentials/data/snapshots
- `auth setup` no longer writes to site-packages directory

## [2.1.0] - 2026-03-27

### Added
- `GADS_CURRENCY` env var (ISO 4217, default: USD)
- Dynamic versioning from `gads_lib.__version__`

### Changed
- CLI logic moved into `gads_lib/cli.py` — proper pip install
- DB columns: `cost_aed` → `cost`, `budget_aed` → `budget`

### Fixed
- `pip install` broken by invalid build backend and missing CLI module

## [2.0.0] - 2026-03-26

### Added
- Google Business Profile: `gbp accounts`, `locations`, `location`, `reviews`, `reply-review`, `delete-reply`
- Google Merchant Center: `merchant account`, `status`, `products`, `product-status`, `feeds`, `shipping`, `returns`
- Google Analytics 4: `ga4 metadata`, `report`, `realtime`
- Modular library (`gads_lib/`), `doctor`, `auth status`, agent enforcement
- `fetch_daily.py`, `generate_token.py`, `pyproject.toml`, `--json` on all commands

### Changed
- All config via environment variables — zero hardcoded values

## [1.0.0] - 2026-02-11

### Added
- Initial CLI: `query`, `log`, `snapshot`, `perf`, `config`, `refresh`
- Google Ads GAQL queries, SQLite database, OAuth credentials

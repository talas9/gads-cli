# Release Notes — gads-cli v3.4.0 → v3.8.2

This document summarises all changes shipped between v3.4.0 and v3.8.2.
For the full per-version changelog see [CHANGELOG.md](CHANGELOG.md).

---

## What's new in v3.4.0 – v3.8.2

### Analyze suite (v3.4.0)

Five new read-only analysis commands, zero account mutations:

| Command | What it does |
|---------|-------------|
| `analyze landing-page` | Fetches a branch landing page and scores it 0–100 on message-match, trust signals, mobile/viewport, load weight, WhatsApp/branch CTA, and `?branch=` survival |
| `analyze wasted-spend` | AED-ranked zero-conversion and below-average-CPA spend on search terms and campaigns |
| `analyze ngrams` | 1/2/3-gram clustering of search terms (Arabic + English) — surfaces high-cost negative-keyword candidates |
| `analyze ad-copy` | Performance-ranks RSA ads and validates against PARTS-ONLY business rules; flags violations by severity |
| `analyze competition` | Impression-share competitive pressure (IS, top-IS, abs-top-IS, rank-lost IS) per keyword; graceful degradation when auction-insight fields are absent |

New sub-package: `gads_lib/analyze/` (lp_score, wasted_spend, ngrams, adcopy, competitive).

---

### Agent-driveable CLI (v3.5.0)

The CLI is now fully self-describing for LLM agents:

- **`gads catalog --json`** — emits a complete machine-readable manifest of every command, subcommand, param, type, default, and help string by walking the live Click tree. Agents must call this first; do not hardcode command lists.
- **Structured error envelope + stable exit codes** — `{"error":{"code":...,"message":...,"exit_code":N}}` on stderr under `--json`. Codes: 0 OK, 1 GENERAL, 2 USAGE, 3 AUTH, 4 NOT_FOUND, 5 API, 6 VALIDATION, 7 DB.
- **History-DB read-only passthrough:** `gads db "<SQL>"`, `gads changelog`, `gads decisions`, `gads milestones` — SELECT-only, enforced at parse time and with `PRAGMA query_only`. Exit code 6 on mutating SQL.
- **`--json` on `log`, `snapshot`, `refresh`** — all commands now structured.
- **Global `--plain` / `--quiet`** — deterministic no-colour output for parsing.
- **`AGENTS.md` and `llms.txt`** committed at CLI root — capability index + LLM-optimised quick reference.

---

### Latest-of-all migration (v3.6.0)

Every external API bumped to its current stable version:

| API | Old | New | Notes |
|-----|-----|-----|-------|
| Google Ads REST | v19 | **v24** | v19 sunset 2026-02-11; keyword forecast request body rebuilt for v24 schema |
| Merchant Center | Content API v2.1 | **Merchant API v1** | Content API v2.1 sunsets 2026-08-18; `--json` shape changed (see CHANGELOG) |
| `requests` | 2.32.3 | **2.34.2** | Closes CVE-2024-47081 and CVE-2026-25645 |
| `python-dotenv` | 1.0.1 | **1.2.2** | Closes CVE-2026-28684 |

Keyword ideas request payload also corrected to the documented REST schema (was HTTP 400 for all inputs).

---

### GA4 / GBP / GSC endpoint coverage (v3.7.0)

New GA4 commands:
- `ga4 batch-report` — up to 5 reports in a single API call (quota savings)
- `ga4 pivot-report` — cross-tabulation with configurable pivot dimension
- `ga4 check-compatibility` — pre-validate dimension+metric combinations

New GSC commands:
- `gsc inspect URL -s SITE` — URL Inspection API (index status, mobile usability, last crawl)
- `gsc sitemaps -s SITE` — list submitted sitemaps
- All existing GSC analytics commands now support `--data-state`, `startRow` pagination, and server-side `dimensionFilterGroups`

New GBP commands:
- `gbp batch-reviews` — fetch reviews from multiple locations in one call
- `gbp local-posts` — list local posts (v4 legacy API)
- `gbp create-post` / `gbp delete-post` — local post CRUD

KB drift check:
- `gads kb check` — compares API versions hard-coded in service modules against `kb/manifest.json`; exits non-zero on drift; CI-able
- `gads kb list` — list KB files with sizes
- `gads kb show <slug>` — print any KB doc

---

### Comprehensive KB + code ↔ KB refs (v3.8.0)

- All five KB files expanded to ~2x size (5,793 → 10,764 total lines), each gaining a **Developer Guide** section covering schemas, enums, request/response shapes, workflows, limits, and error patterns — sufficient for an LLM agent to implement against any of the five APIs without re-fetching docs.
- 44 cross-reference annotations added to the five service modules (`ads.py`, `ga4.py`, `gbp.py`, `gsc.py`, `merchant.py`): module-level docstrings citing KB file + official doc URL, plus per-function `# KB: kb/<slug>.md § <section>` comments.
- GA4 Admin API migrated from `v1alpha` → `v1beta` (stable, no breaking changes); `gads kb check` now exits 0 on first run.
- GSC `webmasters.readonly` scope added to `generate_token.py` (root cause of GSC 403 errors).
- Test suite: 58 tests added (total 58, all pass, offline/CI-safe).

---

### Graceful access-error handling (v3.8.1 + v3.8.2)

All Google API call sites now route through a 4-class error classifier:

| Error class | Trigger | Response |
|-------------|---------|----------|
| `API_NOT_ENABLED` | 403 SERVICE_DISABLED | Names the service; offers `gcloud services enable` interactively |
| `MERCHANT_NOT_REGISTERED` | 401 GCP_NOT_REGISTERED | Shows registration link |
| `INSUFFICIENT_SCOPE` | 403 INSUFFICIENT_AUTHENTICATION_SCOPES | Names the exact missing scope; instructs `python generate_token.py` |
| `PERMISSION_DENIED` | 403 PERMISSION_DENIED / 429 zero-quota | Advises allowlist request with GBP/IAM console link |

Under `--json`: errors emit a classified JSON envelope `{"error":{"code":...,"message":...,"action":...}}` to stdout, exit code 5. Under human mode: advisory text to stderr, interactive `gcloud` offer (suppressed in JSON mode). Never a traceback.

`conversion upload` now surfaces partial failures (HTTP 200 with `partialFailureError`) as a warning (human) or `{"status":"partial_failure",...}` JSON, exit 1 — previously silently ignored.

**Test coverage: 127 tests** (all offline/CI-safe) — covers request-construction correctness, `--json` output structure, error-envelope behaviour, and `gads kb check` alignment across all five service modules.

---

## Known pending items

- **Merchant live verification** — `merchant *` commands are implemented and tested offline, but live verification requires `merchantapi.googleapis.com` to be enabled on the GCP project. Enable via `gcloud services enable merchantapi.googleapis.com` or Cloud Console → APIs & Services. The `API_NOT_ENABLED` graceful error will guide you.
- **GSC live verification** — `gsc inspect` and `gsc sitemaps` require a token regenerated with the `webmasters.readonly` scope (added in v3.8.0). Run `gads auth login --force` or `python generate_token.py`.

---

## Command count

| Version | Commands |
|---------|---------|
| v3.3.0 | 75 |
| v3.4.0 | 80 (+5 analyze) |
| v3.5.0 | 84 (+4 agent-driveable: catalog, db, changelog, decisions, milestones) |
| v3.7.0 | 99 (+15 GA4 batch/pivot/compat, GSC inspect/sitemaps, GBP batch-reviews/local-posts/create-post/delete-post, KB check/list/show) |
| **v3.8.2** | **108** |

# gads-cli

**Google Ads CLI** — a unified command-line tool for managing Google Ads campaigns, with built-in support for Google Business Profile, Google Merchant Center, and Google Analytics (GA4).

Built for AI coding agents (Claude Code, Cursor, etc.) and human operators. Every command supports `--json` for machine-readable output and `--help` for full documentation.

> The name `gads` stands for **G**oogle **Ads**. While Google Ads is the primary focus, the CLI also provides commands for related Google services (GBP, Merchant Center, GA4) that are commonly used alongside ad campaigns.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)

## Features

**65 commands** across 14 groups covering the full Google Ads operational surface:

| Group | Commands | Description |
|-------|----------|-------------|
| **Core** | `query`, `perf`, `config`, `refresh`, `snapshot`, `log`, `accounts`, `doctor` | GAQL queries, local DB reports, campaign snapshots, changelog, account listing |
| **Campaign** | `campaign list`, `status`, `budget`, `perf` | List, enable/pause, change budget, campaign-level metrics from API |
| **Ad Group** | `adgroup list`, `status`, `create` | List, enable/pause, create ad groups |
| **Ad** | `ad list`, `status`, `perf` | List ads with creatives, enable/pause, ad-level metrics |
| **Keyword** | `keyword list`, `add`, `remove`, `negative`, `search-terms`, `ideas`★, `forecast`★ | Keyword management, search terms report, Keyword Planner research |
| **Asset** | `asset list`, `sitelink`, `callout`, `call` | List assets, add sitelinks/callouts/call extensions (two-step creation) |
| **Conversion** | `conversion list`, `create`, `tag`, `perf`, `upload` | Conversion actions, tracking tags, performance by action, offline upload |
| **Audience** | `audience list`, `create`, `upload`, `job-status` | Customer Match user lists, CSV upload with SHA-256 hashing + consent |
| **Report** | `report geo`, `hourly`, `devices`, `search-terms` | Geographic, hourly, device, and search term performance breakdowns |
| **Mutate** | `mutate <type> <json>`, `batch-mutate <json>` | Generic escape hatch for any Google Ads API mutation |
| **GBP** | `gbp accounts`, `locations`, `location`, `reviews`, `reply-review`, `delete-reply` | Google Business Profile management — no dev token needed |
| **Merchant** | `merchant account`, `status`, `products`, `product-status`, `feeds`, `shipping`, `returns` | Merchant Center diagnostics — no dev token needed |
| **GA4** | `ga4 report`, `realtime`, `metadata` | Google Analytics 4 reporting — no dev token needed |
| **Auth** | `auth status`, `setup`, `login`, `revoke`, `test` | Interactive setup wizard, OAuth flow, credential diagnostics |

> ★ Requires Standard Access developer token

**Cross-cutting:**
- `--json` on every command for machine-readable output
- `--dry-run` and `--yes` on all mutation commands
- Auto-logging to changelog after successful mutations
- Scope-aware config — auto-detects project (`./`) vs global (`~/.config/gads/`)
- Agent caller enforcement for multi-agent architectures (optional)
- Configurable timezone (IANA) and currency (ISO 4217)

## Install

One command — downloads the CLI, detects your AI platforms (Claude Code, gsd-pi, ruflo), installs agents + skills + hooks, and runs auth setup:

```bash
curl -fsSL https://raw.githubusercontent.com/talas9/gads-cli/main/scripts/install.sh | bash
```

The installer is interactive. It will:
1. Download the CLI to `~/.gads-cli/`
2. Install Python dependencies
3. Detect Claude Code, gsd-pi, and ruflo
4. Ask which platforms to wire up (global or project scope)
5. Install a specialized `google-platform-operator` agent + `gads-cli` skill + update hook
6. Run the OAuth setup wizard

### Manual Setup

If you prefer manual installation:

```bash
git clone https://github.com/talas9/gads-cli.git
cd gads-cli
pip install .
cp .env.example .env && $EDITOR .env
python generate_token.py
./gads doctor
```

## Setup

### 1. Prerequisites

- Python 3.10+
- A Google Cloud project with APIs enabled (see below)
- OAuth 2.0 client credentials (`client_secret.json`)
- A Google Ads developer token (from a [Manager Account / MCC](https://ads.google.com/intl/en/home/tools/manager-accounts/)) — **required for all Google Ads API commands**, but not needed for GBP, Merchant Center, or GA4

### Google Cloud Project Setup

1. **Create a project** (if you don't have one): [console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate)

2. **Enable APIs** — click each link and click "ENABLE":

   | API | Required for | Link |
   |-----|-------------|------|
   | Google Ads API | **Required** — all ads commands | [Enable](https://console.cloud.google.com/apis/library/googleads.googleapis.com) |
   | My Business Account Mgmt API | GBP commands | [Enable](https://console.cloud.google.com/apis/library/mybusinessaccountmanagement.googleapis.com) |
   | My Business Business Info API | GBP location details | [Enable](https://console.cloud.google.com/apis/library/mybusinessbusinessinformation.googleapis.com) |
   | My Business v4 (legacy) | GBP reviews, posts, media | [Enable](https://console.cloud.google.com/apis/library/mybusiness.googleapis.com) |
   | Content API for Shopping | Merchant Center commands | [Enable](https://console.cloud.google.com/apis/library/content.googleapis.com) |
   | GA4 Data API | GA4 reports and realtime | [Enable](https://console.cloud.google.com/apis/library/analyticsdata.googleapis.com) |
   | GA4 Admin API | GA4 property metadata | [Enable](https://console.cloud.google.com/apis/library/analyticsadmin.googleapis.com) |

   > You only need to enable the APIs for services you'll use. Google Ads API is required; the rest are optional.

3. **Configure OAuth consent screen**:
   - Go to [APIs & Services → OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent)
   - User Type: **External** (unless you have Google Workspace → Internal)
   - App name: anything (e.g. `gads-cli`)
   - User support email & developer contact: your email
   - Click "SAVE AND CONTINUE" through Scopes
   - On **Test Users**: add your Google account email
   - Click "SAVE AND CONTINUE" → "BACK TO DASHBOARD"
   - Your app stays in "Testing" mode — this is fine, you do NOT need to publish or verify it

4. **Create OAuth credentials**:
   - Go to [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
   - Click **+ CREATE CREDENTIALS** → **OAuth client ID**
   - Application type: **Desktop app**
   - Name: anything (e.g. `gads-cli`)
   - Click **CREATE**, then **DOWNLOAD JSON**
   - Save the file as `credentials/client_secret.json` in your project

### Developer Token Access Levels

Your Google Ads developer token determines which API features you can use and how many operations you can perform daily:

| Level | Approval | Ops/day | Production | Features | Notes |
|-------|----------|---------|------------|----------|-------|
| **Test Account** | Instant | 15,000 | Test only | All basic features | Free tier for testing |
| **Explorer** | Auto-granted in some cases | 2,880 prod / 15,000 test | Yes | Most features | Sufficient for basic automation |
| **Basic Access** | Apply, ~2 biz days | 15,000 | Yes | Campaign mgmt, audience mgmt, reporting, keyword research | Most users need this level |
| **Standard Access** | Apply, ~10 biz days | Unlimited | Yes | Everything in Basic + Keyword Planner, Audience Insights, Reach Planner, Billing | Required for advanced features |

### Developer Token is REQUIRED

**For Google Ads API commands:** Developer token is absolutely required. It is NOT optional. Without it, ALL Google Ads operations will fail.

**For other services:** GBP, Merchant Center, and GA4 commands do NOT require a developer token — they only need OAuth credentials.

### Restricted Features (Require Standard Access)

These features require Standard Access level:
- **Keyword Planner** — `gads keyword ideas`, generate keyword ideas with search volume estimates
- **Keyword Forecasting** — `gads keyword forecast`, forecast search volume and CPC
- **Audience Insights** — audience composition and demographics
- **Reach & Frequency Planner** — media buying planning
- **Billing API** — PaymentsAccountService, BillingSetupService, InvoiceService
- **Account Creation** — CustomerService.CreateCustomerClient (creating new ad accounts)
- **User Management** — CustomerUserAccessService (granting users account access)

### Important: Customer Match API Deprecation (April 1, 2026)

**Starting April 1, 2026, uploading Customer Match data via `OfflineUserDataJobService` will fail if your developer token has never sent a successful Customer Match request before.** 

If you plan to use `gads audience upload`, either:
1. Upload before April 1, 2026 to establish token eligibility, OR
2. Use the Data Manager API instead (requires different OAuth scopes and API calls)

### How to Get Your Developer Token

1. **Create a Manager (MCC) account** if you don't have one — developer tokens are created from manager accounts, NOT from regular Google Ads accounts:
   - Go to [ads.google.com/intl/en/home/tools/manager-accounts](https://ads.google.com/intl/en/home/tools/manager-accounts/)
   - Create a manager account (free, takes 2 minutes)
   - Link your Google Ads account(s) to the manager account

2. **Log into your manager account** and go to [Google Ads API Center](https://ads.google.com/aw/apicenter)

3. **Apply for access:**
   - If you see "Apply for Basic Access" → apply and wait for approval (1-3 business days)
   - If you're already approved, your developer token is displayed

4. **For Keyword Planner features only:** After Basic Access is approved, apply for Standard Access. Google reviews your API usage history and this typically takes 1-4 weeks.

5. **Copy your developer token** and set `GOOGLE_ADS_DEVELOPER_TOKEN` in your `.env`

> **Important:** The developer token lives in your *manager account* (MCC). The `GOOGLE_ADS_LOGIN_CUSTOMER_ID` in your `.env` should be set to the manager account's customer ID. The `GOOGLE_ADS_CUSTOMER_ID` is the actual ad account you want to manage.

### 2. Install

**Option A: pip install (recommended)**
```bash
pip install .
```

**Option B: Direct dependencies**
```bash
pip install click requests google-auth google-auth-oauthlib python-dotenv
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env` with your values. At minimum you need:
```bash
GOOGLE_ADS_DEVELOPER_TOKEN=your-developer-token
GOOGLE_ADS_CUSTOMER_ID=1234567890    # 10 digits, no dashes
```

### 4. Generate OAuth token

Place your `client_secret.json` in the `credentials/` directory, then:

```bash
python generate_token.py
```

This opens a browser for Google sign-in and generates `credentials/google-ads-oauth.json` with scopes for all four services (Ads, GBP, Merchant Center, GA4).

### 5. Verify

```bash
./gads doctor
```

## Command Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `gads doctor` | Check credentials, API access, and configuration |
| `gads auth status` | Show credential status (never prints secrets) |
| `gads --version` | Show CLI version |

### Google Ads

```bash
# Run any GAQL query
gads query "SELECT campaign.name, metrics.clicks FROM campaign"

# Performance from local database
gads perf --days 7
gads perf --campaign "my-campaign" --json

# Pull fresh data from API into local DB
gads refresh --days 3
gads refresh --days 7 --config --push

# Snapshot campaign configs before making changes
gads snapshot pre-budget-change --save-file

# Log a change to the changelog
gads log "budget_change" "PMax budget 25→30" --reason "Strong CPA"

# Show current campaign configs from API
gads config --json
```

### Google Business Profile

```bash
# List all GBP accounts
gads gbp accounts

# List locations for an account
gads gbp locations --account accounts/123456789

# Get a specific location's details
gads gbp location locations/987654321

# List reviews for a location
gads gbp reviews locations/987654321

# Reply to a review
gads gbp reply-review accounts/123/locations/456/reviews/789 "Thank you!"

# Delete a review reply
gads gbp delete-reply accounts/123/locations/456/reviews/789
```

### Google Merchant Center

```bash
# Account info
gads merchant account

# Account diagnostics and issues
gads merchant status

# List products
gads merchant products --limit 50

# Product approval statuses
gads merchant product-status

# Data feeds
gads merchant feeds

# Shipping settings
gads merchant shipping

# Return policies
gads merchant returns
```

### Google Analytics (GA4)

```bash
# Available dimensions and metrics
gads ga4 metadata

# Run a report
gads ga4 report --dimensions date --metrics activeUsers,sessions --start 7daysAgo --end yesterday

# Real-time data
gads ga4 realtime --dimensions country --metrics activeUsers
```

### Automation

```bash
# Daily data fetch (use with cron)
python fetch_daily.py --days 3
python fetch_daily.py --days 7 --config --push

# Cron example (fetch at 3:30 AM daily):
# 30 3 * * * cd /path/to/project && python gads-cli/fetch_daily.py --days 3 --push
```

## Configuration Reference

| Variable | Required For | Scope | Description |
|----------|----------|---------|-------------|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads API commands | Google Ads only | Developer token from [Google Ads API Center](https://ads.google.com/aw/apicenter) — absolutely required for ALL ads operations |
| `GOOGLE_ADS_CUSTOMER_ID` | Google Ads API commands | Google Ads only | 10-digit account ID (no dashes) |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | MCC/manager setups | Google Ads only | Manager (MCC) account ID — required if using multi-account setup |
| `GOOGLE_ADS_API_VERSION` | Optional | Google Ads | Default: `v19` |
| `GOOGLE_MERCHANT_CENTER_ID` | Merchant Center commands | Merchant Center | Account ID from Merchant Center dashboard |
| `GOOGLE_GA4_PROPERTY_ID` | GA4 commands | GA4 | Property ID (digits only) — e.g. `271773771` |
| `GADS_TIMEZONE` | Optional | All | IANA timezone (default: `UTC`, examples: `America/New_York`, `Asia/Dubai`, `Europe/London`) |
| `GADS_CURRENCY` | Optional | All | ISO 4217 currency code (default: `USD`, examples: `AED`, `EUR`, `GBP`) |
| `GADS_PROJECT_ROOT` | Optional | All | Project root directory override — auto-detected if not set |
| `GADS_DB_PATH` | Optional | All | SQLite database path (default: `../data/gads.db`) |
| `GADS_CREDENTIALS_PATH` | Optional | All | OAuth token path (default: `../credentials/google-ads-oauth.json`) |
| `GADS_SNAPSHOTS_DIR` | Optional | All | Snapshot output directory (default: `../snapshots`) |

### Command Requirements

| Commands | Needs dev token? | Needs OAuth? | Min access level |
|----------|-----------------|-------------|-----------------|
| `gads gbp *` | No | Yes (business.manage) | N/A |
| `gads merchant *` | No | Yes (content) | N/A |
| `gads ga4 *` | No | Yes (analytics.readonly) | N/A |
| `gads query`, `perf`, `config`, `refresh`, `snapshot`, `log` | Yes | Yes (adwords) | Explorer |
| `gads campaign *`, `gads adgroup *`, `gads ad *`, `gads conversion *`, `gads audience list`, `gads report *` | Yes | Yes (adwords) | Explorer |
| `gads keyword add`, `keyword remove`, `keyword negative`, `keyword search-terms` | Yes | Yes (adwords) | Explorer |
| `gads keyword ideas` | Yes | Yes (adwords) | **Standard** |
| `gads keyword forecast` | Yes | Yes (adwords) | **Standard** |
| `gads audience upload` | Yes | Yes (adwords) | Basic (note: April 2026 Customer Match deprecation) |
| `gads asset *`, `gads campaign budget`, `gads campaign status`, `gads adgroup create`, `gads adgroup status` | Yes | Yes (adwords) | Explorer |

### Agent Enforcement (Optional)

For multi-agent setups where you want to restrict CLI access to a specific agent:

```bash
GADS_ENFORCE_CALLER=1
GADS_EXPECTED_CALLER=my-operator-agent
GADS_CALLER_AGENT=my-operator-agent  # Set by the calling agent
```

When `GADS_ENFORCE_CALLER=1`, the CLI verifies `GADS_CALLER_AGENT` matches `GADS_EXPECTED_CALLER` before executing any command.

## Architecture

```
gads-cli/
├── gads                  # Main CLI entry point (Click)
├── gads.sh               # Shell wrapper with .env loading
├── gads_lib/
│   ├── __init__.py       # Public API — re-exports all modules
│   ├── cli.py            # Entry point for pip-installed command
│   ├── config.py         # Environment-driven configuration
│   ├── auth.py           # OAuth credential management
│   ├── http.py           # HTTP helpers with auth headers
│   ├── ads.py            # Google Ads GAQL client
│   ├── gbp.py            # Google Business Profile client
│   ├── merchant.py       # Merchant Center client
│   ├── ga4.py            # GA4 Data API client
│   ├── db.py             # SQLite connection manager
│   ├── output.py         # Table/JSON formatters
│   └── timeutil.py       # Timezone-aware time helpers
├── fetch_daily.py        # Cron-friendly daily data fetcher
├── generate_token.py     # OAuth token generator (4 scopes)
├── pyproject.toml        # Python package configuration
├── .env.example          # Configuration template
├── CLAUDE.md             # Claude Code project context
├── CHANGELOG.md          # Version history
└── README.md             # This file
```

## Using with Claude Code

This CLI is designed to work seamlessly with [Claude Code](https://claude.ai/code). The included `CLAUDE.md` provides Claude with full context about the CLI's commands, architecture, and configuration.

```bash
# Claude can use the CLI directly:
claude "Run gads perf --days 7 and analyze the trends"
claude "Check my GBP reviews and draft replies for any negative ones"
claude "Pull fresh data and compare this week vs last week"
```

For automated agent workflows, use the agent enforcement feature to restrict CLI access to a designated operator agent.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run the doctor check (`./gads doctor`)
5. Commit and push
6. Open a Pull Request

## License

MIT — see [LICENSE](LICENSE) for details.

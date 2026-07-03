---
name: gads-cli
description: >
  Google Ads, Google Business Profile (GBP), Merchant Center, GA4, and Search
  Console management via gads-cli — campaigns/ad groups/ads/keywords/audiences,
  performance reporting, structural/compliance audits, GBP reviews and
  locations, Merchant Center product feeds, GA4 reports and key events, and
  Search Console analytics/URL inspection. Trigger on mentions of Google Ads,
  Google Business Profile, Merchant Center, GA4, Search Console, campaign
  performance, or keyword/search-term analysis.
---

# gads-cli

`gads` is the CLI for managing Google Ads and the adjacent Google marketing/measurement
surfaces (GBP, Merchant Center, GA4, Search Console). Its knowledge base lives in
`gads-cli/kb/` (sister to `mads-cli/kb/` for Meta Ads).

## Discovery first

Before assuming any command shape, run discovery — do not guess flags or subcommands:

1. `gads catalog --json` — full machine-readable manifest of every implemented command, its
   params, and help text. This is the ground truth for what `gads` can actually do today; the
   CLI is fully wired (verified live via `gads catalog --json`, 2026-07-02): **32 top-level
   command groups**, including dedicated `campaign`/`adgroup`/`ad`/`ads`/`keyword`/`asset`/
   `audience`/`conversion` resource commands (CRUD + status/budget), plus `analyze` and `audit`
   (structural/compliance checks), `gbp`, `merchant`, `ga4`, `gsc` (Search Console) service
   groups — alongside the core `auth`, `query`, `mutate`/`batch-mutate`, `snapshot`, `log`,
   `catalog`, `db`, `changelog`, `decisions`, `milestones`, `perf`, `refresh`, `report`,
   `doctor`, `config`, `accounts` commands.
2. `gads kb list` — surfaces the KB files below (also `gads kb show <slug>` to read one, and
   `gads kb check` to verify the KB isn't stale relative to the installed API versions).

## Deep API reference (read on demand, not preloaded)

See `kb/INDEX.md` for the full index — Google Ads REST API, Merchant API, GA4 Data + Admin
APIs, Google Business Profile suite, and Search Console API — each with current version, OAuth
scopes, and a Developer Guide section. Read the specific KB file for the resource you're
touching before writing code against it — do not rely on training-data knowledge of these APIs,
which change frequently.

## Operating directive: run it yourself

Execute `gads` commands yourself — don't hand the user copy-paste console/CLI steps to run
manually. The user's involvement is reduced to the irreducible minimum: only steps a script
genuinely cannot perform, such as clicking "Allow" in an interactive OAuth consent browser
flow, or another physical/off-system action. For those, still do everything around the human
step yourself — run the local server, generate and hand over the exact URL, wait for the
callback, then verify the result. Default to action over instruction.

## Sister tool

For **Meta (Facebook/Instagram) Ads** — Marketing API campaigns/ad sets/ads/creatives, Business
Manager, Conversions API (CAPI), and Commerce Manager — see the sister CLI **mads-cli**:
https://github.com/talas9/mads-cli

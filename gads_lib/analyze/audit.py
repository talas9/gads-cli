"""Structural-compliance audit — 12 sections, 0/50/100 scoring.

Inspired by Optmyzr audit findings documented in:
  reports/talas-optimization-proposal.md

Each section scores 0, 50, or 100.
Final score = weighted average of all 12 sections.

READ-ONLY: only ``run_gaql`` (read) is used.  Nothing here mutates the account.
Date window always ends YESTERDAY (24-48h attribution lag).

Sections
--------
 1. rsa_headline_length      — RSA headlines ≤ 30 chars  (0/50/100)
 2. rsa_description_length   — RSA descriptions ≤ 90 chars
 3. rsa_headline_diversity   — Intra-RSA duplicate-headline detection
 4. rsa_ad_strength          — Ad Strength EXCELLENT/GOOD vs POOR/AVERAGE
 5. dki_presence             — Dynamic Keyword Insertion in ≥1 ad
 6. ad_schedule              — Campaign-level ad-schedule criteria present
 7. attribution_model        — Conversions NOT using Last-Click
 8. budget_lost_is           — search_budget_lost_impression_share < 20%
 9. keyword_qs               — QS sub-signal distribution (post-click, creative, predicted_ctr)
10. negative_coverage        — Shared or campaign-level negative keywords present
11. conversion_primary       — ≥1 conversion action set as primary
12. sitelink_coverage        — ≥1 sitelink asset per active SEARCH campaign
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from ..ads import run_gaql
from ..output import print_table, print_json


# ---------------------------------------------------------------------------
# Section weights (must sum to 100)
# ---------------------------------------------------------------------------
_WEIGHTS: dict[str, int] = {
    "rsa_headline_length":    10,
    "rsa_description_length":  8,
    "rsa_headline_diversity":  8,
    "rsa_ad_strength":         8,
    "dki_presence":            6,
    "ad_schedule":            10,
    "attribution_model":      12,
    "budget_lost_is":         10,
    "keyword_qs":              8,
    "negative_coverage":       8,
    "conversion_primary":      8,
    "sitelink_coverage":       4,
}

assert sum(_WEIGHTS.values()) == 100, "Section weights must sum to 100"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _window(days: int) -> tuple[str, str]:
    """Return (d_from, d_to) YYYY-MM-DD. d_to = yesterday."""
    d_to = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return d_from, d_to


def _score(val: int) -> int:
    """Clamp to valid 0/50/100 domain."""
    if val <= 0:
        return 0
    if val >= 100:
        return 100
    return 50


def _extract_texts(asset_list: list[dict]) -> list[str]:
    return [item["text"] for item in asset_list if isinstance(item, dict) and "text" in item]


_RE_DKI = re.compile(r"\{keyword:", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Section scorers — each returns (score: int, details: dict)
# ---------------------------------------------------------------------------

def _check_rsa_headline_length(ads: list[dict]) -> tuple[int, dict]:
    """Score 100 if all headlines ≤ 30 chars; 50 if some over; 0 if >25% over."""
    if not ads:
        return 50, {"note": "No RSA ads found in window", "over_limit": 0, "total": 0}

    over_count = 0
    total_count = 0
    examples: list[str] = []
    for ad in ads:
        for h in ad.get("headlines", []):
            total_count += 1
            if len(h) > 30:
                over_count += 1
                if len(examples) < 3:
                    examples.append(f"{h!r} ({len(h)} chars)")

    if total_count == 0:
        return 50, {"note": "No headline text found", "over_limit": 0, "total": 0}

    pct = over_count / total_count
    if pct == 0:
        s = 100
    elif pct <= 0.25:
        s = 50
    else:
        s = 0

    return s, {
        "over_limit": over_count,
        "total": total_count,
        "pct_over": round(pct * 100, 1),
        "examples": examples,
    }


def _check_rsa_description_length(ads: list[dict]) -> tuple[int, dict]:
    """Score 100 if all descriptions ≤ 90 chars; 50 if some over; 0 if >25% over."""
    if not ads:
        return 50, {"note": "No RSA ads found in window", "over_limit": 0, "total": 0}

    over_count = 0
    total_count = 0
    examples: list[str] = []
    for ad in ads:
        for d in ad.get("descriptions", []):
            total_count += 1
            if len(d) > 90:
                over_count += 1
                if len(examples) < 3:
                    examples.append(f"{repr(d[:60])}… ({len(d)} chars)")

    if total_count == 0:
        return 50, {"note": "No description text found", "over_limit": 0, "total": 0}

    pct = over_count / total_count
    if pct == 0:
        s = 100
    elif pct <= 0.25:
        s = 50
    else:
        s = 0

    return s, {
        "over_limit": over_count,
        "total": total_count,
        "pct_over": round(pct * 100, 1),
        "examples": examples,
    }


def _check_rsa_headline_diversity(ads: list[dict]) -> tuple[int, dict]:
    """Score 100 if no ad has intra-RSA duplicate headlines; 50 if ≤25% do; 0 otherwise."""
    if not ads:
        return 50, {"note": "No RSA ads found", "ads_with_dupes": 0, "total_ads": 0}

    ads_with_dupes = 0
    examples: list[dict] = []
    for ad in ads:
        headlines = [h.lower().strip() for h in ad.get("headlines", [])]
        seen: set[str] = set()
        dupes: list[str] = []
        for h in headlines:
            if h in seen and h not in dupes:
                dupes.append(h)
            seen.add(h)
        if dupes:
            ads_with_dupes += 1
            if len(examples) < 3:
                examples.append({
                    "ad_id": ad.get("ad_id", ""),
                    "campaign": ad.get("campaign", ""),
                    "duplicates": dupes[:3],
                })

    pct = ads_with_dupes / len(ads)
    if pct == 0:
        s = 100
    elif pct <= 0.25:
        s = 50
    else:
        s = 0

    return s, {
        "ads_with_dupes": ads_with_dupes,
        "total_ads": len(ads),
        "pct_affected": round(pct * 100, 1),
        "examples": examples,
    }


def _check_rsa_ad_strength(ads: list[dict]) -> tuple[int, dict]:
    """Score 100 if all ads EXCELLENT/GOOD; 50 if some AVERAGE; 0 if any POOR.

    NOTE: ad_group_ad.ad_strength is available on the ad_group_ad resource.
    KB confirmed (kb/google-ads.md): GAQL field = ad_group_ad.ad_strength;
    REST JSON key = adGroupAd.adStrength (camelCase, read-only). Parsed correctly.
    """
    if not ads:
        return 50, {"note": "No RSA ads found", "excellent_good": 0, "average": 0, "poor": 0}

    counts: dict[str, int] = {"EXCELLENT": 0, "GOOD": 0, "AVERAGE": 0, "POOR": 0, "UNKNOWN": 0}
    for ad in ads:
        strength = str(ad.get("ad_strength", "UNKNOWN")).upper()
        if strength in counts:
            counts[strength] += 1
        else:
            counts["UNKNOWN"] += 1

    total = len(ads)
    if counts["POOR"] > 0:
        s = 0
    elif counts["AVERAGE"] > 0:
        s = 50
    elif counts["EXCELLENT"] + counts["GOOD"] > 0:
        s = 100
    else:
        s = 50  # all unknown — data unavailable

    return s, {**counts, "total": total}


def _check_dki_presence(ads: list[dict]) -> tuple[int, dict]:
    """Score 100 if ≥1 ad uses DKI; 0 otherwise."""
    dki_ads: list[str] = []
    for ad in ads:
        all_text = " ".join(ad.get("headlines", []) + ad.get("descriptions", []))
        if _RE_DKI.search(all_text):
            dki_ads.append(ad.get("ad_id", "?"))

    if dki_ads:
        return 100, {"dki_ad_count": len(dki_ads), "examples": dki_ads[:5]}
    return 0, {
        "dki_ad_count": 0,
        "note": "No DKI ({keyword:...}) found in any RSA ad — consider adding for Search campaigns",
    }


def _check_ad_schedule(creds, d_from: str, d_to: str) -> tuple[int, dict]:
    """Score 100 if ≥1 SEARCH campaign has ad-schedule criteria; 50 if partial; 0 if none.

    Queries campaign_criterion for ad schedule entries.
    """
    rows = run_gaql(creds, f"""
        SELECT campaign.name,
               campaign.status,
               campaign_criterion.type,
               campaign_criterion.ad_schedule.day_of_week,
               campaign_criterion.ad_schedule.start_hour
        FROM campaign_criterion
        WHERE campaign_criterion.type = 'AD_SCHEDULE'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
        LIMIT 200
    """)

    # Also get total active SEARCH campaigns for denominator
    camp_rows = run_gaql(creds, f"""
        SELECT campaign.name, campaign.status
        FROM campaign
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status = 'ENABLED'
        LIMIT 50
    """)

    active_campaigns: set[str] = set()
    for r in camp_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            active_campaigns.add(name)

    scheduled_campaigns: set[str] = set()
    for r in rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            scheduled_campaigns.add(name)

    total = len(active_campaigns)
    scheduled = len(scheduled_campaigns & active_campaigns)

    if total == 0:
        return 50, {"note": "No active SEARCH campaigns found", "scheduled": 0, "total": 0}

    pct = scheduled / total
    if pct == 1.0:
        s = 100
    elif pct > 0:
        s = 50
    else:
        s = 0

    return s, {
        "scheduled": scheduled,
        "total": total,
        "pct_scheduled": round(pct * 100, 1),
        "unscheduled_campaigns": sorted(active_campaigns - scheduled_campaigns),
    }


def _check_attribution_model(creds) -> tuple[int, dict]:
    """Score 100 if all conversions use DATA_DRIVEN; 50 if any use LAST_CLICK; 0 if all LAST_CLICK.

    Uses conversion_action resource.
    """
    rows = run_gaql(creds, """
        SELECT conversion_action.name,
               conversion_action.status,
               conversion_action.attribution_model_settings.attribution_model,
               conversion_action.counting_type
        FROM conversion_action
        WHERE conversion_action.status = 'ENABLED'
        LIMIT 50
    """)

    if not rows:
        return 50, {"note": "No enabled conversion actions found", "last_click": 0, "total": 0}

    last_click: list[str] = []
    non_last_click: list[str] = []
    for r in rows:
        ca = r.get("conversionAction", {})
        name = ca.get("name", "")
        model_settings = ca.get("attributionModelSettings", {})
        model = model_settings.get("attributionModel", "UNKNOWN")
        if "LAST_CLICK" in str(model).upper():
            last_click.append(name)
        else:
            non_last_click.append(name)

    total = len(last_click) + len(non_last_click)
    if not last_click:
        s = 100
    elif not non_last_click:
        s = 0
    else:
        s = 50

    return s, {
        "last_click_count": len(last_click),
        "non_last_click_count": len(non_last_click),
        "total": total,
        "last_click_actions": last_click[:5],
        "recommendation": (
            "Switch to DATA_DRIVEN attribution — account has >300 conv/month (qualified)"
            if last_click else "Good — no Last-Click attribution in use"
        ),
    }


def _check_budget_lost_is(creds, d_from: str, d_to: str) -> tuple[int, dict]:
    """Score 100 if avg budget_lost_is < 10%; 50 if < 20%; 0 if ≥ 20%.

    search_budget_lost_impression_share is available on the campaign resource.
    """
    rows = run_gaql(creds, f"""
        SELECT campaign.name,
               campaign.status,
               metrics.search_budget_lost_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.search_budget_lost_impression_share DESC
        LIMIT 50
    """)

    # Aggregate per campaign (may have date segments)
    agg: dict[str, dict] = {}
    for r in rows:
        c = r.get("campaign", {})
        m = r.get("metrics", {})
        name = c.get("name", "")
        if not name:
            continue
        raw = m.get("searchBudgetLostImpressionShare")
        try:
            val = float(raw) if raw is not None else None
            # Sentinel value check (API sometimes returns huge int for "unavailable")
            if val is not None and (val > 1.5 or val < 0):
                val = None
        except (TypeError, ValueError):
            val = None

        if name not in agg:
            agg[name] = {"sum": 0.0, "n": 0, "status": c.get("status", "")}
        if val is not None:
            agg[name]["sum"] += val
            agg[name]["n"] += 1

    if not agg:
        return 50, {"note": "No SEARCH campaign budget-IS data in window", "campaigns": []}

    campaigns = []
    for name, d in agg.items():
        avg_val = (d["sum"] / d["n"] * 100) if d["n"] > 0 else None
        campaigns.append({
            "campaign": name,
            "budget_lost_is_pct": round(avg_val, 1) if avg_val is not None else None,
        })
    campaigns.sort(key=lambda x: (x["budget_lost_is_pct"] or 0), reverse=True)

    valid = [c["budget_lost_is_pct"] for c in campaigns if c["budget_lost_is_pct"] is not None]
    avg = sum(valid) / len(valid) if valid else None

    if avg is None:
        s = 50
    elif avg < 10:
        s = 100
    elif avg < 20:
        s = 50
    else:
        s = 0

    return s, {
        "avg_budget_lost_is_pct": round(avg, 1) if avg is not None else None,
        "threshold_100": "< 10%",
        "threshold_50": "10–20%",
        "campaigns": campaigns,
    }


def _check_keyword_qs(creds, d_from: str, d_to: str) -> tuple[int, dict]:
    """Score 100 if avg QS ≥ 7; 50 if ≥ 5; 0 if < 5.

    Uses keyword_view with QS sub-signals.
    TODO: KB field — ad_group_criterion.quality_info.quality_score (and sub-signals)
    available on keyword_view resource.
    """
    rows = run_gaql(creds, f"""
        SELECT ad_group_criterion.keyword.text,
               ad_group_criterion.quality_info.quality_score,
               ad_group_criterion.quality_info.post_click_quality_score,
               ad_group_criterion.quality_info.creative_quality_score,
               ad_group_criterion.quality_info.search_predicted_ctr,
               campaign.status,
               ad_group.status,
               ad_group_criterion.status,
               metrics.impressions
        FROM keyword_view
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
          AND ad_group.status != 'REMOVED'
          AND ad_group_criterion.status != 'REMOVED'
        LIMIT 200
    """)

    qs_values: list[int] = []
    sub_signal_counts: dict[str, dict[str, int]] = {
        "post_click": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
        "creative": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
        "predicted_ctr": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
    }
    seen_kw: set[str] = set()  # deduplicate

    for r in rows:
        kw = r.get("adGroupCriterion", {})
        qi = kw.get("qualityInfo", {})
        kw_text = kw.get("keyword", {}).get("text", "")

        if kw_text and kw_text not in seen_kw:
            seen_kw.add(kw_text)
            qs = qi.get("qualityScore")
            if qs is not None:
                try:
                    qs_values.append(int(qs))
                except (TypeError, ValueError):
                    pass

        def _accum(key: str, api_key: str) -> None:
            val = str(qi.get(api_key, "UNKNOWN")).upper()
            if val in sub_signal_counts[key]:
                sub_signal_counts[key][val] += 1
            else:
                sub_signal_counts[key]["UNKNOWN"] += 1

        _accum("post_click", "postClickQualityScore")
        _accum("creative", "creativeQualityScore")
        _accum("predicted_ctr", "searchPredictedCtr")

    if not qs_values:
        return 50, {
            "note": "No QS data available in window — may need impressions to show",
            "avg_qs": None,
            "sub_signals": sub_signal_counts,
        }

    avg_qs = sum(qs_values) / len(qs_values)
    if avg_qs >= 7:
        s = 100
    elif avg_qs >= 5:
        s = 50
    else:
        s = 0

    return s, {
        "avg_qs": round(avg_qs, 2),
        "qs_values_count": len(qs_values),
        "threshold_100": "≥ 7",
        "threshold_50": "5–6",
        "sub_signals": sub_signal_counts,
    }


def _check_negative_coverage(creds) -> tuple[int, dict]:
    """Score 100 if ≥1 shared negative list or campaign-level negatives exist; 0 otherwise.

    Checks shared_set resource for NEGATIVE_KEYWORDS type, and campaign_criterion
    for negative keywords.
    """
    # Check shared negative keyword lists
    shared_rows = run_gaql(creds, """
        SELECT shared_set.name, shared_set.type, shared_set.member_count
        FROM shared_set
        WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
          AND shared_set.status = 'ENABLED'
        LIMIT 20
    """)

    shared_lists = []
    for r in shared_rows:
        ss = r.get("sharedSet", {})
        shared_lists.append({
            "name": ss.get("name", ""),
            "member_count": int(ss.get("memberCount", 0)),
        })

    # Check campaign-level negative keywords
    neg_rows = run_gaql(creds, """
        SELECT campaign.name,
               campaign.status,
               campaign_criterion.keyword.text,
               campaign_criterion.negative,
               campaign_criterion.type
        FROM campaign_criterion
        WHERE campaign_criterion.negative = true
          AND campaign_criterion.type = 'KEYWORD'
          AND campaign.status != 'REMOVED'
        LIMIT 50
    """)

    campaigns_with_negatives: set[str] = set()
    for r in neg_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            campaigns_with_negatives.add(name)

    has_shared = len(shared_lists) > 0
    has_campaign = len(campaigns_with_negatives) > 0

    if has_shared or has_campaign:
        s = 100
    else:
        s = 0

    return s, {
        "shared_negative_lists": len(shared_lists),
        "shared_lists_detail": shared_lists[:5],
        "campaigns_with_campaign_level_negatives": len(campaigns_with_negatives),
        "campaigns_list": sorted(campaigns_with_negatives)[:5],
    }


def _check_conversion_primary(creds) -> tuple[int, dict]:
    """Score 100 if ≥1 conversion action is set as primary (non-secondary); 0 otherwise.

    Uses conversion_action.primary_for_goal / counting_type.
    KB checked (kb/google-ads.md): conversion_action.primary_for_goal is NOT
    documented in the KB. Field availability/name is unconfirmed for API v24.
    Category proxy is retained as the reliable fallback.
    """
    rows = run_gaql(creds, """
        SELECT conversion_action.name,
               conversion_action.status,
               conversion_action.counting_type,
               conversion_action.category
        FROM conversion_action
        WHERE conversion_action.status = 'ENABLED'
        LIMIT 50
    """)

    if not rows:
        return 50, {"note": "No enabled conversion actions found", "primary": 0, "total": 0}

    primary_actions: list[str] = []
    secondary_actions: list[str] = []
    for r in rows:
        ca = r.get("conversionAction", {})
        name = ca.get("name", "")
        counting_type = str(ca.get("countingType", "")).upper()
        # MANY_PER_CLICK or ONE_PER_CLICK = primary; SECONDARY is not a real API value
        # The API uses primary_for_goal boolean — but proxy: any enabled action is
        # considered primary unless explicitly marked SECONDARY via the UI category.
        category = str(ca.get("category", "")).upper()
        if category in ("DEFAULT", "PURCHASE", "SUBMIT_LEAD_FORM", "PHONE_CALL_LEAD",
                        "IMPORTED_LEAD", "QUALIFIED_LEAD", "CONVERTED_LEAD",
                        "SIGNUP", "BEGIN_CHECKOUT", "SUBSCRIBE_PAID",
                        "ADD_TO_CART", "STORE_VISIT", "OTHER"):
            primary_actions.append(name)
        else:
            secondary_actions.append(name)

    if primary_actions:
        s = 100
    else:
        s = 0

    return s, {
        "primary": len(primary_actions),
        "total": len(primary_actions) + len(secondary_actions),
        "primary_actions": primary_actions[:5],
        "note": (
            "KB (kb/google-ads.md) does not document conversion_action.primary_for_goal; "
            "field availability unconfirmed for API v24 — category proxy retained"
        ),
    }


def _check_sitelink_coverage(creds, d_from: str, d_to: str) -> tuple[int, dict]:
    """Score 100 if all active SEARCH campaigns have ≥1 sitelink; 50 if partial; 0 if none.

    Queries campaign_asset for sitelink type assets linked to SEARCH campaigns.
    """
    # Get active SEARCH campaigns
    camp_rows = run_gaql(creds, f"""
        SELECT campaign.name, campaign.status
        FROM campaign
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status = 'ENABLED'
        LIMIT 50
    """)

    active_campaigns: set[str] = set()
    for r in camp_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            active_campaigns.add(name)

    if not active_campaigns:
        return 50, {"note": "No active SEARCH campaigns found", "covered": 0, "total": 0}

    # Get campaigns with sitelink assets.
    # NOTE: campaign_asset.asset_type is not selectable in GAQL; use asset.type instead.
    # Join campaign_asset with asset to get the type via the asset resource.
    # Any field used in WHERE must also appear in SELECT (API v24 requirement).
    asset_rows = run_gaql(creds, """
        SELECT campaign.name,
               campaign.status,
               asset.type,
               campaign_asset.status
        FROM campaign_asset
        WHERE asset.type = 'SITELINK'
          AND campaign.status != 'REMOVED'
          AND campaign_asset.status != 'REMOVED'
        LIMIT 200
    """)

    campaigns_with_sitelinks: set[str] = set()
    for r in asset_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            campaigns_with_sitelinks.add(name)

    covered = len(active_campaigns & campaigns_with_sitelinks)
    total = len(active_campaigns)
    pct = covered / total

    if pct == 1.0:
        s = 100
    elif pct > 0:
        s = 50
    else:
        s = 0

    return s, {
        "covered": covered,
        "total": total,
        "pct_covered": round(pct * 100, 1),
        "missing_sitelinks": sorted(active_campaigns - campaigns_with_sitelinks),
    }


# ---------------------------------------------------------------------------
# RSA ad fetcher (shared between sections 1-5)
# ---------------------------------------------------------------------------

def _fetch_rsa_ads(creds, d_from: str, d_to: str, limit: int = 100) -> list[dict]:
    """Fetch RSA ads with headlines, descriptions, ad strength, metrics."""
    rows = run_gaql(creds, f"""
        SELECT ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.ad_strength,
               ad_group_ad.status,
               campaign.name,
               ad_group.name,
               metrics.impressions
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND ad_group_ad.status != 'REMOVED'
          AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
        ORDER BY metrics.impressions DESC
        LIMIT {limit}
    """)

    # Deduplicate by ad_id
    seen: dict[str, dict] = {}
    for row in rows:
        ada = row.get("adGroupAd", {})
        ad = ada.get("ad", {})
        ad_id = str(ad.get("id", ""))
        if not ad_id:
            continue
        if ad_id in seen:
            continue

        rsa = ad.get("responsiveSearchAd", {})
        headlines = _extract_texts(rsa.get("headlines", []))
        descriptions = _extract_texts(rsa.get("descriptions", []))
        seen[ad_id] = {
            "ad_id": ad_id,
            "campaign": row.get("campaign", {}).get("name", ""),
            "ad_group": row.get("adGroup", {}).get("name", ""),
            "status": ada.get("status", ""),
            "ad_strength": ada.get("adStrength", "UNKNOWN"),
            "headlines": headlines,
            "descriptions": descriptions,
        }

    return list(seen.values())


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def analyze_audit(creds, days: int = 30) -> dict:
    """Run the 12-section structural-compliance audit.

    Parameters
    ----------
    creds : OAuth credentials from gads_lib.get_credentials()
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    {
      "window": {"from": str, "to": str, "days": int},
      "overall_score": int,           # 0-100 weighted average
      "grade": str,                   # A/B/C/D/F
      "sections": [
        {
          "id": str,                  # section key
          "name": str,                # human-readable name
          "score": int,               # 0 / 50 / 100
          "weight": int,              # % of final score
          "weighted_contribution": float,
          "status": str,              # "pass" / "partial" / "fail"
          "details": dict,            # section-specific findings
        }, ...
      ],
      "sections_by_id": {str: {...}}, # same data keyed by id for agent access
      "summary": {
          "pass": int,
          "partial": int,
          "fail": int,
          "critical_fails": [str],    # ids of sections scoring 0
      }
    }
    """
    from ..config import CURRENCY

    d_from, d_to = _window(days)

    # Fetch RSA ads once — shared by sections 1-5
    rsa_ads = _fetch_rsa_ads(creds, d_from, d_to)

    # Run each section
    raw_sections: dict[str, tuple[int, dict]] = {}

    raw_sections["rsa_headline_length"] = _check_rsa_headline_length(rsa_ads)
    raw_sections["rsa_description_length"] = _check_rsa_description_length(rsa_ads)
    raw_sections["rsa_headline_diversity"] = _check_rsa_headline_diversity(rsa_ads)
    raw_sections["rsa_ad_strength"] = _check_rsa_ad_strength(rsa_ads)
    raw_sections["dki_presence"] = _check_dki_presence(rsa_ads)
    raw_sections["ad_schedule"] = _check_ad_schedule(creds, d_from, d_to)
    raw_sections["attribution_model"] = _check_attribution_model(creds)
    raw_sections["budget_lost_is"] = _check_budget_lost_is(creds, d_from, d_to)
    raw_sections["keyword_qs"] = _check_keyword_qs(creds, d_from, d_to)
    raw_sections["negative_coverage"] = _check_negative_coverage(creds)
    raw_sections["conversion_primary"] = _check_conversion_primary(creds)
    raw_sections["sitelink_coverage"] = _check_sitelink_coverage(creds, d_from, d_to)

    # Human-readable section names
    _NAMES: dict[str, str] = {
        "rsa_headline_length":    "RSA Headline Length (≤30 chars)",
        "rsa_description_length": "RSA Description Length (≤90 chars)",
        "rsa_headline_diversity": "RSA Intra-Ad Duplicate Headlines",
        "rsa_ad_strength":        "RSA Ad Strength (Excellent/Good)",
        "dki_presence":           "Dynamic Keyword Insertion (DKI)",
        "ad_schedule":            "Ad Schedule / Dayparting",
        "attribution_model":      "Conversion Attribution Model",
        "budget_lost_is":         "Budget-Lost Impression Share",
        "keyword_qs":             "Keyword Quality Score Distribution",
        "negative_coverage":      "Negative Keyword Coverage",
        "conversion_primary":     "Primary Conversion Action",
        "sitelink_coverage":      "Sitelink Asset Coverage",
    }

    # Assemble sections list
    sections = []
    total_weighted = 0.0
    pass_count = partial_count = fail_count = 0
    critical_fails: list[str] = []

    for sec_id in _WEIGHTS:
        score, details = raw_sections[sec_id]
        weight = _WEIGHTS[sec_id]
        contribution = score * weight / 100
        total_weighted += contribution

        if score == 100:
            status = "pass"
            pass_count += 1
        elif score == 50:
            status = "partial"
            partial_count += 1
        else:
            status = "fail"
            fail_count += 1
            critical_fails.append(sec_id)

        sections.append({
            "id": sec_id,
            "name": _NAMES[sec_id],
            "score": score,
            "weight": weight,
            "weighted_contribution": round(contribution, 2),
            "status": status,
            "details": details,
        })

    overall = int(round(total_weighted))

    if overall >= 85:
        grade = "A"
    elif overall >= 70:
        grade = "B"
    elif overall >= 55:
        grade = "C"
    elif overall >= 40:
        grade = "D"
    else:
        grade = "F"

    sections_by_id = {s["id"]: s for s in sections}

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "overall_score": overall,
        "grade": grade,
        "sections": sections,
        "sections_by_id": sections_by_id,
        "summary": {
            "pass": pass_count,
            "partial": partial_count,
            "fail": fail_count,
            "critical_fails": critical_fails,
        },
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def render_audit(result: dict, as_json: bool = False) -> None:
    """Print audit report to stdout.

    If as_json=True, dumps the full result dict as JSON.
    Otherwise prints:
      1. Section scorecard table
      2. Per-section findings for non-passing sections
      3. Overall score + grade
    """
    import click

    if as_json:
        return print_json(result)

    w = result["window"]
    overall = result["overall_score"]
    grade = result["grade"]
    summary = result["summary"]

    # Colour map
    grade_colors = {"A": "green", "B": "green", "C": "yellow", "D": "yellow", "F": "red"}
    score_colors = {100: "green", 50: "yellow", 0: "red"}

    click.secho(
        f"\nStructural Compliance Audit — {w['from']} → {w['to']} ({w['days']}d)",
        fg="yellow", bold=True,
    )
    click.echo(
        f"  Sections: {summary['pass']} pass  |  "
        f"{summary['partial']} partial  |  "
        f"{summary['fail']} fail"
    )

    # Scorecard table
    click.secho("\nSection scorecard:", fg="white", bold=True)
    table_rows = []
    for s in result["sections"]:
        table_rows.append({
            "#": s["id"],
            "section": s["name"][:40],
            "score": s["score"],
            "weight": f"{s['weight']}%",
            "contrib": f"{s['weighted_contribution']:.1f}",
            "status": s["status"].upper(),
        })
    print_table(table_rows, ["#", "section", "score", "weight", "contrib", "status"])

    # Findings for non-passing sections
    non_pass = [s for s in result["sections"] if s["status"] != "pass"]
    if non_pass:
        click.secho("\nFindings (partial / fail sections):", fg="white", bold=True)
        for s in non_pass:
            status_fg = "red" if s["status"] == "fail" else "yellow"
            click.secho(
                f"\n  [{s['status'].upper()}] {s['name']} — score {s['score']}/100",
                fg=status_fg, bold=True,
            )
            details = s["details"]
            # Print key findings from details
            if "note" in details:
                click.echo(f"    Note: {details['note']}")
            if "examples" in details and details["examples"]:
                click.echo(f"    Examples: {details['examples'][:3]}")
            if "recommendation" in details:
                click.echo(f"    Recommendation: {details['recommendation']}")
            if "unscheduled_campaigns" in details and details["unscheduled_campaigns"]:
                click.echo(f"    Unscheduled campaigns: {', '.join(details['unscheduled_campaigns'][:5])}")
            if "missing_sitelinks" in details and details["missing_sitelinks"]:
                click.echo(f"    Missing sitelinks: {', '.join(details['missing_sitelinks'][:5])}")
            if "last_click_actions" in details and details["last_click_actions"]:
                click.echo(f"    Last-click conversions: {', '.join(details['last_click_actions'][:3])}")
            if "avg_budget_lost_is_pct" in details and details["avg_budget_lost_is_pct"] is not None:
                click.echo(f"    Avg budget-lost IS: {details['avg_budget_lost_is_pct']}%")
            if "avg_qs" in details and details["avg_qs"] is not None:
                click.echo(f"    Avg Quality Score: {details['avg_qs']}")

    # Overall score
    click.echo()
    score_fg = score_colors.get(50, "cyan")
    if overall >= 85:
        score_fg = "green"
    elif overall >= 55:
        score_fg = "yellow"
    else:
        score_fg = "red"

    click.secho("  Overall score: ", nl=False)
    click.secho(f"{overall}/100  Grade: {grade}", fg=score_fg, bold=True)
    click.echo()

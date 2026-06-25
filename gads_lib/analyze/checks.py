"""Standalone read-only gap checks for Google Ads accounts.

Seven independent check functions, each returning a dict suitable for
``--json`` output.  Nothing here mutates the account — only ``run_gaql``
(SELECT-only GAQL) is used.

Date windows always end YESTERDAY to respect the 24-48h attribution lag.

Checks
------
1. check_rsa_lengths       — headlines < 20 chars or descriptions < 60 chars
2. check_rsa_duplicates    — same headline text twice in one RSA (case-insensitive)
3. check_dki_presence      — Dynamic Keyword Insertion usage (or absence)
4. check_ad_schedule       — SEARCH campaigns missing ad-schedule criteria
5. check_attribution_model — conversion actions still on LAST_CLICK
6. check_budget_lost_is    — search_budget_lost_impression_share > 10%
7. check_qs_distribution   — QS band distribution + sub-signal breakdown
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from ..ads import run_gaql
from ..config import CURRENCY
from ..output import print_table, print_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _window(days: int) -> tuple[str, str]:
    """Return (d_from, d_to) as YYYY-MM-DD strings. d_to is always yesterday."""
    d_to = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return d_from, d_to


def _extract_texts(asset_list: list[dict]) -> list[str]:
    """Extract .text from a list of headline/description asset dicts."""
    return [item["text"] for item in asset_list if isinstance(item, dict) and "text" in item]


_RE_DKI = re.compile(r"\{keyword:", re.IGNORECASE)


def _fetch_rsa_ads(creds, d_from: str, d_to: str, limit: int = 200) -> list[dict]:
    """Fetch RSA ads (deduplicated by ad_id) for the given date window."""
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

    seen: dict[str, dict] = {}
    for row in rows:
        ada = row.get("adGroupAd", {})
        ad = ada.get("ad", {})
        ad_id = str(ad.get("id", ""))
        if not ad_id or ad_id in seen:
            continue
        rsa = ad.get("responsiveSearchAd", {})
        seen[ad_id] = {
            "ad_id": ad_id,
            "campaign": row.get("campaign", {}).get("name", ""),
            "ad_group": row.get("adGroup", {}).get("name", ""),
            "status": ada.get("status", ""),
            "ad_strength": ada.get("adStrength", "UNKNOWN"),
            "headlines": _extract_texts(rsa.get("headlines", [])),
            "descriptions": _extract_texts(rsa.get("descriptions", [])),
        }
    return list(seen.values())


# ---------------------------------------------------------------------------
# 1. check_rsa_lengths
# ---------------------------------------------------------------------------

def check_rsa_lengths(creds, days: int = 30) -> dict:
    """Flag RSA headlines < 20 chars or descriptions < 60 chars.

    Google's character *limits* are 30/90; this check flags the opposite problem
    — copy that is too short and likely hurts ad strength.

    Parameters
    ----------
    creds : OAuth credentials from ``gads_lib.get_credentials()``
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with window, counts, flagged items, percentages, and impact level.
    """
    d_from, d_to = _window(days)
    ads = _fetch_rsa_ads(creds, d_from, d_to)

    total_ads = len(ads)
    total_headlines = 0
    total_descriptions = 0
    short_headlines: list[dict] = []
    short_descriptions: list[dict] = []

    for ad in ads:
        for h in ad.get("headlines", []):
            total_headlines += 1
            if len(h) < 20:
                short_headlines.append({
                    "ad_id": ad["ad_id"],
                    "campaign": ad["campaign"],
                    "headline": h,
                    "length": len(h),
                })
        for d in ad.get("descriptions", []):
            total_descriptions += 1
            if len(d) < 60:
                short_descriptions.append({
                    "ad_id": ad["ad_id"],
                    "campaign": ad["campaign"],
                    "description": d,
                    "length": len(d),
                })

    pct_h = (len(short_headlines) / total_headlines * 100) if total_headlines > 0 else 0.0
    pct_d = (len(short_descriptions) / total_descriptions * 100) if total_descriptions > 0 else 0.0
    pct_max = max(pct_h, pct_d)

    if pct_max > 25:
        impact = "HIGH"
    elif pct_max > 0:
        impact = "MEDIUM"
    else:
        impact = "INFO"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "currency": CURRENCY,
        "total_ads": total_ads,
        "total_headlines": total_headlines,
        "total_descriptions": total_descriptions,
        "short_headlines": short_headlines,
        "short_descriptions": short_descriptions,
        "pct_headlines_short": round(pct_h, 1),
        "pct_descriptions_short": round(pct_d, 1),
        "impact": impact,
    }


# ---------------------------------------------------------------------------
# 2. check_rsa_duplicates
# ---------------------------------------------------------------------------

def check_rsa_duplicates(creds, days: int = 30) -> dict:
    """Find RSA ads where the same headline text appears more than once (case-insensitive).

    Parameters
    ----------
    creds : OAuth credentials
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with affected ads list, count, and impact.
    """
    d_from, d_to = _window(days)
    ads = _fetch_rsa_ads(creds, d_from, d_to)

    ads_with_duplicates: list[dict] = []

    for ad in ads:
        headlines = [h.lower().strip() for h in ad.get("headlines", [])]
        seen: set[str] = set()
        dupes: list[str] = []
        for h in headlines:
            if h in seen and h not in dupes:
                dupes.append(h)
            seen.add(h)
        if dupes:
            ads_with_duplicates.append({
                "ad_id": ad["ad_id"],
                "campaign": ad["campaign"],
                "ad_group": ad["ad_group"],
                "duplicate_headlines": dupes,
            })

    impact = "HIGH" if ads_with_duplicates else "INFO"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "total_ads": len(ads),
        "ads_with_duplicates": ads_with_duplicates,
        "count_affected": len(ads_with_duplicates),
        "impact": impact,
    }


# ---------------------------------------------------------------------------
# 3. check_dki_presence
# ---------------------------------------------------------------------------

def check_dki_presence(creds, days: int = 30) -> dict:
    """Check for Dynamic Keyword Insertion syntax in RSA headlines or descriptions.

    Looks for ``{KeyWord:`` / ``{keyword:`` in any ad text.  Absence is flagged
    as a MEDIUM recommendation — DKI can improve relevance for Search campaigns.

    Parameters
    ----------
    creds : OAuth credentials
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with dki_found flag, matching ads, and recommendation.
    """
    d_from, d_to = _window(days)
    ads = _fetch_rsa_ads(creds, d_from, d_to)

    ads_with_dki: list[dict] = []

    for ad in ads:
        all_text = " ".join(ad.get("headlines", []) + ad.get("descriptions", []))
        m = _RE_DKI.search(all_text)
        if m:
            ads_with_dki.append({
                "ad_id": ad["ad_id"],
                "campaign": ad["campaign"],
                "snippet": m.group(0),
            })

    dki_found = len(ads_with_dki) > 0

    if dki_found:
        recommendation = "DKI is in use — review placements to confirm correct default text."
        impact = "INFO"
    else:
        recommendation = (
            "No Dynamic Keyword Insertion found. Consider adding {KeyWord:Default} to at "
            "least one headline per Search campaign to improve ad relevance."
        )
        impact = "MEDIUM"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "dki_found": dki_found,
        "ads_with_dki": ads_with_dki,
        "total_ads_checked": len(ads),
        "impact": impact,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# 4. check_ad_schedule
# ---------------------------------------------------------------------------

def check_ad_schedule(creds, days: int = 30) -> dict:
    """Check which active SEARCH campaigns are missing ad-schedule criteria.

    Campaigns with no ad schedule may waste budget during off-hours.

    Parameters
    ----------
    creds : OAuth credentials
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with coverage stats, unscheduled campaign names, and impact.
    """
    d_from, d_to = _window(days)

    # Active SEARCH campaigns
    camp_rows = run_gaql(creds, f"""
        SELECT campaign.name, campaign.status
        FROM campaign
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status = 'ENABLED'
        LIMIT 100
    """)

    active_campaigns: set[str] = set()
    for r in camp_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            active_campaigns.add(name)

    # Campaigns that have at least one AD_SCHEDULE criterion
    sched_rows = run_gaql(creds, """
        SELECT campaign.name,
               campaign_criterion.type
        FROM campaign_criterion
        WHERE campaign_criterion.type = 'AD_SCHEDULE'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
        LIMIT 200
    """)

    scheduled_campaigns: set[str] = set()
    for r in sched_rows:
        name = r.get("campaign", {}).get("name", "")
        if name:
            scheduled_campaigns.add(name)

    total = len(active_campaigns)
    scheduled = len(scheduled_campaigns & active_campaigns)
    unscheduled = sorted(active_campaigns - scheduled_campaigns)
    coverage_pct = (scheduled / total * 100) if total > 0 else 100.0

    if coverage_pct < 50:
        impact = "HIGH"
    elif coverage_pct < 100:
        impact = "MEDIUM"
    else:
        impact = "INFO"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "total_search_campaigns": total,
        "scheduled_campaigns": scheduled,
        "unscheduled_campaigns": unscheduled,
        "coverage_pct": round(coverage_pct, 1),
        "impact": impact,
    }


# ---------------------------------------------------------------------------
# 5. check_attribution_model
# ---------------------------------------------------------------------------

def check_attribution_model(creds) -> dict:
    """Check conversion actions for LAST_CLICK attribution (vs DATA_DRIVEN).

    Parameters
    ----------
    creds : OAuth credentials

    Returns
    -------
    dict with per-model action lists and recommendation.
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

    last_click_actions: list[dict] = []
    data_driven_actions: list[str] = []
    other_actions: list[str] = []

    for r in rows:
        ca = r.get("conversionAction", {})
        name = ca.get("name", "")
        model_settings = ca.get("attributionModelSettings", {})
        model = str(model_settings.get("attributionModel", "UNKNOWN")).upper()

        if "LAST_CLICK" in model:
            last_click_actions.append({"name": name, "model": model})
        elif "DATA_DRIVEN" in model:
            data_driven_actions.append(name)
        else:
            other_actions.append(name)

    impact = "HIGH" if last_click_actions else "INFO"
    recommendation = (
        "Switch flagged actions to DATA_DRIVEN attribution — it better weights all touchpoints."
        if last_click_actions
        else "Good — no LAST_CLICK attribution actions found."
    )

    return {
        "total_conversion_actions": len(last_click_actions) + len(data_driven_actions) + len(other_actions),
        "last_click_actions": last_click_actions,
        "data_driven_actions": data_driven_actions,
        "other_actions": other_actions,
        "impact": impact,
        "recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# 6. check_budget_lost_is
# ---------------------------------------------------------------------------

def check_budget_lost_is(creds, days: int = 30) -> dict:
    """Flag SEARCH campaigns with search_budget_lost_impression_share > 10%.

    API returns values as 0.0–1.0 ratios.  Sentinel values > 1.5 mean "data
    unavailable" and are set to None.

    Parameters
    ----------
    creds : OAuth credentials
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with per-campaign list, average, flagged count, and impact.
    """
    d_from, d_to = _window(days)

    rows = run_gaql(creds, f"""
        SELECT campaign.name,
               campaign.status,
               metrics.search_budget_lost_impression_share
        FROM campaign
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.search_budget_lost_impression_share DESC
        LIMIT 100
    """)

    # Aggregate per campaign (window may return date-segmented rows)
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
            if val is not None and (val > 1.5 or val < 0):
                val = None
        except (TypeError, ValueError):
            val = None

        if name not in agg:
            agg[name] = {"sum": 0.0, "n": 0}
        if val is not None:
            agg[name]["sum"] += val
            agg[name]["n"] += 1

    campaigns: list[dict] = []
    for name, d in agg.items():
        avg_pct = (d["sum"] / d["n"] * 100) if d["n"] > 0 else None
        rounded = round(avg_pct, 1) if avg_pct is not None else None
        campaigns.append({
            "name": name,
            "budget_lost_is_pct": rounded,
            "flag": (rounded is not None and rounded > 10),
        })
    campaigns.sort(key=lambda x: (x["budget_lost_is_pct"] or 0), reverse=True)

    valid = [c["budget_lost_is_pct"] for c in campaigns if c["budget_lost_is_pct"] is not None]
    avg = (sum(valid) / len(valid)) if valid else None
    avg_rounded = round(avg, 1) if avg is not None else None
    flagged_count = sum(1 for c in campaigns if c["flag"])

    if avg is None:
        impact = "INFO"
    elif avg > 20:
        impact = "HIGH"
    elif avg > 10:
        impact = "MEDIUM"
    else:
        impact = "INFO"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "campaigns": campaigns,
        "avg_budget_lost_is_pct": avg_rounded,
        "flagged_count": flagged_count,
        "impact": impact,
    }


# ---------------------------------------------------------------------------
# 7. check_qs_distribution
# ---------------------------------------------------------------------------

def check_qs_distribution(creds, days: int = 30) -> dict:
    """Query keyword QS and sub-signal distributions.

    Sub-signal field mapping (matching audit.py _check_keyword_qs):
      postClickQualityScore  → "post_click"
      creativeQualityScore   → "creative"
      searchPredictedCtr     → "predicted_ctr"

    Keywords are deduplicated by text before computing QS averages.

    Parameters
    ----------
    creds : OAuth credentials
    days  : look-back window ending YESTERDAY (default 30)

    Returns
    -------
    dict with avg_qs, band distribution, sub-signal counts, and impact.
    """
    d_from, d_to = _window(days)

    rows = run_gaql(creds, f"""
        SELECT ad_group_criterion.keyword.text,
               ad_group_criterion.quality_info.quality_score,
               ad_group_criterion.quality_info.post_click_quality_score,
               ad_group_criterion.quality_info.creative_quality_score,
               ad_group_criterion.quality_info.search_predicted_ctr,
               metrics.impressions
        FROM keyword_view
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND campaign.status != 'REMOVED'
          AND ad_group.status != 'REMOVED'
          AND ad_group_criterion.status != 'REMOVED'
        LIMIT 500
    """)

    qs_values: list[int] = []
    qs_dist: dict[str, int] = {"1-3": 0, "4-6": 0, "7-10": 0}
    sub_signals: dict[str, dict[str, int]] = {
        "post_click":    {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
        "creative":      {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
        "predicted_ctr": {"ABOVE_AVERAGE": 0, "AVERAGE": 0, "BELOW_AVERAGE": 0, "UNKNOWN": 0},
    }
    seen_kw: set[str] = set()

    def _accum(key: str, api_key: str, qi: dict) -> None:
        val = str(qi.get(api_key, "UNKNOWN")).upper()
        if val in sub_signals[key]:
            sub_signals[key][val] += 1
        else:
            sub_signals[key]["UNKNOWN"] += 1

    for r in rows:
        kw = r.get("adGroupCriterion", {})
        qi = kw.get("qualityInfo", {})
        kw_text = kw.get("keyword", {}).get("text", "")

        # Deduplicate by keyword text for QS averaging
        if kw_text and kw_text not in seen_kw:
            seen_kw.add(kw_text)
            qs_raw = qi.get("qualityScore")
            if qs_raw is not None:
                try:
                    qs_int = int(qs_raw)
                    qs_values.append(qs_int)
                    if qs_int <= 3:
                        qs_dist["1-3"] += 1
                    elif qs_int <= 6:
                        qs_dist["4-6"] += 1
                    else:
                        qs_dist["7-10"] += 1
                except (TypeError, ValueError):
                    pass

        # Sub-signals accumulate for all rows (not deduplicated)
        _accum("post_click", "postClickQualityScore", qi)
        _accum("creative", "creativeQualityScore", qi)
        _accum("predicted_ctr", "searchPredictedCtr", qi)

    avg_qs: float | None = None
    if qs_values:
        avg_qs = round(sum(qs_values) / len(qs_values), 2)

    if avg_qs is None:
        impact = "INFO"
    elif avg_qs < 5:
        impact = "HIGH"
    elif avg_qs < 7:
        impact = "MEDIUM"
    else:
        impact = "INFO"

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "total_keywords": len(seen_kw),
        "avg_qs": avg_qs,
        "qs_distribution": qs_dist,
        "sub_signals": sub_signals,
        "impact": impact,
    }

"""$-ranked wasted-spend detection (AED).

Wasted spend = money spent on search terms / campaigns that produced
**zero conversions**, OR whose CPA is far worse than the account average
(below-average efficiency — the overspend above an "efficient" cost).

All amounts are in the configured account currency (AED for Talas).
``cost_micros / 1e6`` = AED.

READ-ONLY: only ``run_gaql`` is used. Nothing here mutates the account.
Date window always ends YESTERDAY (never same-day — 24-48h attribution lag).
"""

from datetime import datetime, timedelta

from ..ads import run_gaql
from ..output import print_table, print_json


def _window(days):
    """Return (d_from, d_to) as YYYY-MM-DD strings. d_to = yesterday."""
    d_to = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return d_from, d_to


def analyze_wasted_spend(creds, days: int = 30, min_cost: float = 1.0,
                         cpa_multiple: float = 2.0) -> dict:
    """creds from gads_lib.get_credentials(). Uses run_gaql. days = window ending YESTERDAY.

    Returns: {"window":{"from":...,"to":...,"days":days},
              "avg_cpa": float|None, "currency":"AED",
              "search_terms":[{"search_term","campaign","cost","conv","clicks","wasted","reason"},...],  # sorted desc by wasted
              "campaigns":[{"campaign","cost","conv","wasted","reason"},...],  # sorted desc by wasted
              "totals":{"wasted_search_terms":float,"wasted_campaigns":float}}
    """
    from ..config import CURRENCY

    d_from, d_to = _window(days)
    where_date = f"WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'"

    # ── 1. Campaigns (same window) — used for account-wide avg CPA + campaign buckets.
    camp_rows = run_gaql(creds, f"""
        SELECT campaign.name, campaign.status,
               metrics.cost_micros, metrics.conversions, metrics.conversions_value
        FROM campaign
        {where_date} AND campaign.status != 'REMOVED'
    """)

    # Aggregate per-campaign (a campaign yields one row per date segment? No —
    # without segments.date in SELECT the API still aggregates over the WHERE
    # window, but campaign rows can appear once; aggregate defensively by name).
    camp_agg = {}
    total_cost = 0.0
    total_conv = 0.0
    for r in camp_rows:
        c = r.get("campaign", {})
        m = r.get("metrics", {})
        name = c.get("name", "")
        cost = int(m.get("costMicros", 0)) / 1e6
        conv = float(m.get("conversions", 0))
        cval = float(m.get("conversionsValue", 0))
        agg = camp_agg.setdefault(name, {"cost": 0.0, "conv": 0.0, "cval": 0.0})
        agg["cost"] += cost
        agg["conv"] += conv
        agg["cval"] += cval
        total_cost += cost
        total_conv += conv

    # ── Account-average CPA over the window.
    avg_cpa = (total_cost / total_conv) if total_conv > 0 else None
    cpa_threshold = (avg_cpa * cpa_multiple) if avg_cpa is not None else None

    def _classify(cost, conv):
        """Return (wasted_aed, reason) or (0.0, None) if not wasted."""
        if cost <= 0:
            return 0.0, None
        if conv == 0:
            return cost, "zero_conversion"
        # has conversions — check efficiency vs threshold
        if cpa_threshold is not None:
            cpa = cost / conv
            if cpa > cpa_threshold:
                # overspend above what an efficient (avg-CPA) buy would have cost
                efficient_cost = conv * avg_cpa
                wasted = cost - efficient_cost
                if wasted > 0:
                    return wasted, (
                        f"below_average (cpa {cpa:.2f} > {cpa_multiple:g}x "
                        f"avg {avg_cpa:.2f})"
                    )
        return 0.0, None

    # ── Build campaign list.
    campaigns = []
    for name, agg in camp_agg.items():
        cost = agg["cost"]
        conv = agg["conv"]
        if cost < min_cost:
            continue
        wasted, reason = _classify(cost, conv)
        if wasted <= 0:
            continue
        campaigns.append({
            "campaign": name,
            "cost": round(cost, 2),
            "conv": round(conv, 2),
            "wasted": round(wasted, 2),
            "reason": reason,
        })
    campaigns.sort(key=lambda x: x["wasted"], reverse=True)

    # ── 2. Search terms (same window).
    st_rows = run_gaql(creds, f"""
        SELECT search_term_view.search_term, campaign.name,
               metrics.cost_micros, metrics.conversions, metrics.clicks,
               metrics.conversions_value
        FROM search_term_view
        {where_date}
    """)

    # Aggregate per (search_term, campaign) defensively.
    st_agg = {}
    for r in st_rows:
        st = r.get("searchTermView", {})
        c = r.get("campaign", {})
        m = r.get("metrics", {})
        term = st.get("searchTerm", "")
        camp = c.get("name", "")
        key = (term, camp)
        cost = int(m.get("costMicros", 0)) / 1e6
        conv = float(m.get("conversions", 0))
        clicks = int(m.get("clicks", 0))
        agg = st_agg.setdefault(key, {"cost": 0.0, "conv": 0.0, "clicks": 0})
        agg["cost"] += cost
        agg["conv"] += conv
        agg["clicks"] += clicks

    search_terms = []
    for (term, camp), agg in st_agg.items():
        cost = agg["cost"]
        conv = agg["conv"]
        if cost < min_cost:
            continue
        wasted, reason = _classify(cost, conv)
        if wasted <= 0:
            continue
        search_terms.append({
            "search_term": term,
            "campaign": camp,
            "cost": round(cost, 2),
            "conv": round(conv, 2),
            "clicks": agg["clicks"],
            "wasted": round(wasted, 2),
            "reason": reason,
        })
    search_terms.sort(key=lambda x: x["wasted"], reverse=True)

    totals = {
        "wasted_search_terms": round(sum(x["wasted"] for x in search_terms), 2),
        "wasted_campaigns": round(sum(x["wasted"] for x in campaigns), 2),
    }

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "avg_cpa": (round(avg_cpa, 2) if avg_cpa is not None else None),
        "currency": CURRENCY,
        "search_terms": search_terms,
        "campaigns": campaigns,
        "totals": totals,
    }


def render_wasted_spend(result: dict, as_json: bool = False, limit: int = 25) -> None:
    """Print with print_table/print_json. AED amounts rounded to 2dp.
    If as_json: print_json(result)."""
    import click

    if as_json:
        return print_json(result)

    w = result["window"]
    cur = result.get("currency", "AED")
    avg_cpa = result.get("avg_cpa")
    avg_str = f"{avg_cpa:,.2f} {cur}" if avg_cpa is not None else "n/a"

    click.secho(
        f"\nWasted spend — {w['from']} → {w['to']} ({w['days']}d)  "
        f"account avg CPA: {avg_str}",
        fg="yellow", bold=True,
    )

    click.secho(f"\nTop wasted search terms (by {cur} wasted):", fg="white", bold=True)
    print_table(
        result["search_terms"][:limit],
        ["search_term", "campaign", "cost", "conv", "clicks", "wasted", "reason"],
    )

    click.secho(f"\nTop wasted campaigns (by {cur} wasted):", fg="white", bold=True)
    print_table(
        result["campaigns"][:limit],
        ["campaign", "cost", "conv", "wasted", "reason"],
    )

    t = result["totals"]
    click.secho(
        f"\nTotal wasted — search terms: {t['wasted_search_terms']:,.2f} {cur}  |  "
        f"campaigns: {t['wasted_campaigns']:,.2f} {cur}",
        fg="red", bold=True,
    )

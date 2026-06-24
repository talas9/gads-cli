"""Performance-ranked ad-copy analysis + business-rule validation (AED).

Pulls all active RSA ads with performance metrics over a date window ending
YESTERDAY, ranks them by conversions then CTR, and validates every headline
and description against Talas business rules.

READ-ONLY: only ``run_gaql`` and ``get_db`` (read) are used.  Nothing here
mutates the account.

Business rules checked (from DB + concrete detectors):
  CRITICAL — install/repair/workshop/battery-service words
  CRITICAL — standalone "EV"/"electric vehicle" without "Tesla"
  CRITICAL — "OEM only" / "Genuine only" / "genuine parts only" wording
  HIGH     — UAE phone numbers appearing in copy (flag + branch match)
  HIGH     — "Parts: new + used + aftermarket" rule (OEM/Genuine only)
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from ..ads import run_gaql
from ..output import print_table, print_json

# ── Branch phone numbers (from HANDOVER.md) ─────────────────────────────────
_BRANCH_PHONES: dict[str, str] = {
    "+971566662075": "QZ3",
    "971566662075": "QZ3",
    "0566662075": "QZ3",
    "566662075": "QZ3",
    "+971501996588": "SJA",
    "971501996588": "SJA",
    "0501996588": "SJA",
    "501996588": "SJA",
    "+971564045033": "IND4",
    "971564045033": "IND4",
    "0564045033": "IND4",
    "564045033": "IND4",
}

# Raw digit strings for quick matching
_BRANCH_PHONE_DIGITS: dict[str, str] = {
    "566662075": "QZ3",
    "501996588": "SJA",
    "564045033": "IND4",
}

# ── Compiled regex patterns for rule detection ────────────────────────────────
_RE_INSTALL = re.compile(
    r"\b(install(ation)?|repair|workshop|battery\s+service|"
    r"technician|bring\s+your\s+car|we\s+(fix|repair)|service\s+cent(?:er|re))\b",
    re.IGNORECASE,
)

_RE_EV = re.compile(
    r"\b(EV|electric\s+vehicle|electric\s+car)\b",
    re.IGNORECASE,
)

_RE_TESLA = re.compile(r"\btesla\b", re.IGNORECASE)

_RE_OEM_GENUINE = re.compile(
    r"\b(OEM\s+only|genuine\s+only|genuine\s+parts\s+only|original\s+parts\s+only)\b",
    re.IGNORECASE,
)

# UAE phone pattern: optional country code 971 or 0, then 9 digits
_RE_UAE_PHONE = re.compile(
    r"(?:(?:\+|00)?971|0)\s*(?:\d[\s.-]?){8,9}\d",
)


def _window(days: int) -> tuple[str, str]:
    """Return (d_from, d_to) YYYY-MM-DD. d_to = yesterday."""
    d_to = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return d_from, d_to


def _extract_texts(asset_list: list[dict]) -> list[str]:
    """Extract .text strings from a list of headline/description asset dicts."""
    return [item["text"] for item in asset_list if isinstance(item, dict) and "text" in item]


def _load_rules(conn) -> list[dict]:
    """Load ad_copy and business rules from the DB business_rules table."""
    cur = conn.execute(
        "SELECT id, rule, category, severity, examples "
        "FROM business_rules "
        "WHERE category IN ('ad_copy', 'business') "
        "ORDER BY severity, id"
    )
    return [dict(row) for row in cur.fetchall()]


def _check_text(text: str, rules: list[dict]) -> list[dict]:
    """Run all detectors on a single headline or description text.

    Returns a list of violation dicts:
        {"text", "rule", "rule_id", "severity", "kind", "snippet"}
    """
    violations: list[dict] = []
    text_lower = text.lower()

    # ── 1. Install / repair / workshop / battery-service / service-center ─────
    m = _RE_INSTALL.search(text)
    if m:
        # Find DB rule id for this — rule 1 and rule 3
        rule_row = next(
            (r for r in rules if r["id"] in (1, 3)),
            {"id": 1, "rule": "PARTS ONLY — no install/repair/workshop/battery/service-center language", "severity": "CRITICAL"},
        )
        violations.append({
            "text": text,
            "rule": rule_row["rule"],
            "rule_id": rule_row["id"],
            "severity": "CRITICAL",
            "kind": "install_repair_language",
            "snippet": m.group(0),
        })

    # ── 2. EV / electric vehicle used WITHOUT Tesla ───────────────────────────
    ev_m = _RE_EV.search(text)
    if ev_m and not _RE_TESLA.search(text):
        rule_row = next(
            (r for r in rules if r["id"] == 2),
            {"id": 2, "rule": "Tesla not EV — always Tesla-specific, never generic EV", "severity": "CRITICAL"},
        )
        violations.append({
            "text": text,
            "rule": rule_row["rule"],
            "rule_id": rule_row["id"],
            "severity": "CRITICAL",
            "kind": "ev_not_tesla",
            "snippet": ev_m.group(0),
        })

    # ── 3. OEM only / Genuine only ────────────────────────────────────────────
    oem_m = _RE_OEM_GENUINE.search(text)
    if oem_m:
        rule_row = next(
            (r for r in rules if r["id"] == 9),
            {"id": 9, "rule": "Parts: new + used + aftermarket — NOT OEM only or Genuine only", "severity": "HIGH"},
        )
        violations.append({
            "text": text,
            "rule": rule_row["rule"],
            "rule_id": rule_row["id"],
            "severity": "HIGH",
            "kind": "oem_genuine_only",
            "snippet": oem_m.group(0),
        })

    # ── 4. UAE phone in copy — flag + try to identify branch ─────────────────
    phone_m = _RE_UAE_PHONE.search(text)
    if phone_m:
        raw = phone_m.group(0)
        digits_only = re.sub(r"\D", "", raw)
        # Match last 9 digits against known branch phones
        branch = None
        for suffix, br in _BRANCH_PHONE_DIGITS.items():
            if digits_only.endswith(suffix):
                branch = br
                break
        branch_note = f" (matches {branch})" if branch else " (unknown branch — verify!)"
        rule_row = next(
            (r for r in rules if r["id"] == 7),
            {"id": 7, "rule": "Phone numbers are branch-specific — never mix", "severity": "CRITICAL"},
        )
        violations.append({
            "text": text,
            "rule": rule_row["rule"] + branch_note,
            "rule_id": rule_row["id"],
            "severity": rule_row.get("severity", "HIGH"),
            "kind": "phone_in_copy",
            "snippet": raw,
        })

    return violations


def analyze_adcopy(creds, days: int = 30, top: int = 50) -> dict:
    """Pull RSA ads + performance, rank, and validate against business rules.

    Args:
        creds: credentials from ``gads_lib.get_credentials()``
        days:  lookback window in days, ending YESTERDAY (default 30)
        top:   maximum number of ads to return (default 50)

    Returns::

        {
          "window": {"from": str, "to": str, "days": int},
          "currency": "AED",
          "ads": [
            {
              "ad_id": str,
              "campaign": str,
              "ad_group": str,
              "status": str,
              "impr": int,
              "clicks": int,
              "conv": float,
              "cost": float,         # AED
              "ctr": float,          # 0-1 ratio
              "headlines": [str],
              "descriptions": [str],
              "violations": [
                {"text": str, "rule": str, "rule_id": int,
                 "severity": str, "kind": str, "snippet": str}
              ]
            },
            ...
          ],
          "violations_summary": {"CRITICAL": int, "HIGH": int, "MEDIUM": int, "LOW": int},
          "rules_loaded": int,
        }
    """
    from ..config import CURRENCY
    from ..db import get_db

    d_from, d_to = _window(days)

    # ── Load business rules from DB ───────────────────────────────────────────
    conn = get_db()
    try:
        db_rules = _load_rules(conn)
    finally:
        conn.close()

    # ── Query RSA ads with performance ────────────────────────────────────────
    rows = run_gaql(creds, f"""
        SELECT ad_group_ad.ad.id,
               ad_group_ad.ad.responsive_search_ad.headlines,
               ad_group_ad.ad.responsive_search_ad.descriptions,
               ad_group_ad.status,
               campaign.name,
               ad_group.name,
               metrics.impressions,
               metrics.clicks,
               metrics.conversions,
               metrics.cost_micros,
               metrics.ctr
        FROM ad_group_ad
        WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'
          AND ad_group_ad.status != REMOVED
          AND ad_group_ad.ad.type = RESPONSIVE_SEARCH_AD
        ORDER BY metrics.conversions DESC, metrics.ctr DESC
        LIMIT {top}
    """)

    # ── Aggregate per ad_id (API may return multiple date segments) ───────────
    ad_agg: dict[str, dict] = {}
    for row in rows:
        ada = row.get("adGroupAd", {})
        ad = ada.get("ad", {})
        ad_id = str(ad.get("id", ""))
        if not ad_id:
            continue

        m = row.get("metrics", {})
        cost = int(m.get("costMicros", 0)) / 1e6
        clicks = int(m.get("clicks", 0))
        conv = float(m.get("conversions", 0))
        impr = int(m.get("impressions", 0))
        # ctr from API when present; else compute below
        ctr_api = float(m.get("ctr", 0.0))

        rsa = ad.get("responsiveSearchAd", {})
        headlines = _extract_texts(rsa.get("headlines", []))
        descriptions = _extract_texts(rsa.get("descriptions", []))

        if ad_id not in ad_agg:
            ad_agg[ad_id] = {
                "ad_id": ad_id,
                "campaign": row.get("campaign", {}).get("name", ""),
                "ad_group": row.get("adGroup", {}).get("name", ""),
                "status": ada.get("status", ""),
                "impr": 0,
                "clicks": 0,
                "conv": 0.0,
                "cost": 0.0,
                "_ctr_num": 0,   # weighted clicks for ctr
                "_ctr_den": 0,   # weighted impr for ctr
                "headlines": headlines,
                "descriptions": descriptions,
            }

        entry = ad_agg[ad_id]
        entry["impr"] += impr
        entry["clicks"] += clicks
        entry["conv"] += conv
        entry["cost"] += cost
        entry["_ctr_num"] += clicks
        entry["_ctr_den"] += impr
        # Keep freshest/most complete headlines/descriptions
        if headlines and not entry["headlines"]:
            entry["headlines"] = headlines
        if descriptions and not entry["descriptions"]:
            entry["descriptions"] = descriptions

    # ── Finalise and validate ─────────────────────────────────────────────────
    ads = []
    violations_summary: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for entry in ad_agg.values():
        # Compute CTR from aggregated clicks/impr
        ctr = (entry["_ctr_num"] / entry["_ctr_den"]) if entry["_ctr_den"] > 0 else 0.0

        # Validate all headlines and descriptions
        all_violations: list[dict] = []
        for txt in entry["headlines"] + entry["descriptions"]:
            all_violations.extend(_check_text(txt, db_rules))

        for v in all_violations:
            sev = v.get("severity", "LOW")
            violations_summary[sev] = violations_summary.get(sev, 0) + 1

        ads.append({
            "ad_id": entry["ad_id"],
            "campaign": entry["campaign"],
            "ad_group": entry["ad_group"],
            "status": entry["status"],
            "impr": entry["impr"],
            "clicks": entry["clicks"],
            "conv": round(entry["conv"], 1),
            "cost": round(entry["cost"], 2),
            "ctr": round(ctr, 4),
            "headlines": entry["headlines"],
            "descriptions": entry["descriptions"],
            "violations": all_violations,
        })

    # Sort by conv desc, then ctr desc
    ads.sort(key=lambda x: (x["conv"], x["ctr"]), reverse=True)
    ads = ads[:top]

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "currency": CURRENCY,
        "ads": ads,
        "violations_summary": violations_summary,
        "rules_loaded": len(db_rules),
    }


def render_adcopy(
    result: dict,
    as_json: bool = False,
    top: int = 25,
    violations_only: bool = False,
) -> None:
    """Print ranked ad table + violations table.

    Args:
        result:          Return value of ``analyze_adcopy``.
        as_json:         If True, print raw JSON instead of tables.
        top:             Max ads to show in the ranked table.
        violations_only: If True, only show ads that have violations.
    """
    import click

    if as_json:
        return print_json(result)

    w = result["window"]
    cur = result.get("currency", "AED")
    vs = result.get("violations_summary", {})
    n_ads = len(result["ads"])
    n_viol_ads = sum(1 for a in result["ads"] if a["violations"])

    click.secho(
        f"\nAd-copy analysis — {w['from']} → {w['to']} ({w['days']}d)  "
        f"currency: {cur}",
        fg="yellow", bold=True,
    )
    click.echo(
        f"  {n_ads} RSA ads  |  {n_viol_ads} with violations  |  "
        f"rules loaded: {result['rules_loaded']}"
    )
    click.echo(
        f"  Violations — CRITICAL: {vs.get('CRITICAL', 0)}  "
        f"HIGH: {vs.get('HIGH', 0)}  "
        f"MEDIUM: {vs.get('MEDIUM', 0)}  "
        f"LOW: {vs.get('LOW', 0)}"
    )

    # ── Performance-ranked ad table ───────────────────────────────────────────
    ads_to_show = result["ads"]
    if violations_only:
        ads_to_show = [a for a in ads_to_show if a["violations"]]

    click.secho(
        f"\nPerformance-ranked RSA ads (top {top}"
        + (" — violations only" if violations_only else "")
        + "):",
        fg="white", bold=True,
    )

    table_rows = []
    for ad in ads_to_show[:top]:
        n_v = len(ad["violations"])
        n_crit = sum(1 for v in ad["violations"] if v["severity"] == "CRITICAL")
        viol_flag = (
            f"CRIT:{n_crit}" if n_crit > 0
            else (f"HIGH:{n_v}" if n_v > 0 else "OK")
        )
        table_rows.append({
            "ad_id": ad["ad_id"],
            "campaign": ad["campaign"][:28],
            "ad_group": ad["ad_group"][:20],
            "status": ad["status"],
            "conv": ad["conv"],
            "clicks": ad["clicks"],
            "impr": ad["impr"],
            "ctr%": f"{ad['ctr']*100:.2f}",
            "cost": ad["cost"],
            "violations": viol_flag,
        })

    print_table(
        table_rows,
        ["ad_id", "campaign", "ad_group", "status", "conv", "clicks", "impr", "ctr%", "cost", "violations"],
    )

    # ── Violations detail table ───────────────────────────────────────────────
    all_violations = []
    for ad in result["ads"]:
        for v in ad["violations"]:
            all_violations.append({
                "ad_id": ad["ad_id"],
                "severity": v["severity"],
                "kind": v["kind"],
                "snippet": v.get("snippet", "")[:40],
                "text": v["text"][:50],
                "rule": v["rule"][:60],
            })

    if all_violations:
        click.secho(f"\nViolations detail ({len(all_violations)} total):", fg="red", bold=True)
        # Sort critical first
        all_violations.sort(key=lambda x: (0 if x["severity"] == "CRITICAL" else 1, x["ad_id"]))
        print_table(
            all_violations,
            ["severity", "ad_id", "kind", "snippet", "text", "rule"],
        )
    else:
        click.secho("\nNo business-rule violations found.", fg="green", bold=True)

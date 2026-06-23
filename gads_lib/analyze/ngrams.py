"""N-gram search-term clustering for the Talas gads CLI.

Tokenises every search term in the account's search_term_view, builds
1-gram / 2-gram / 3-gram (or up to ``n``-gram) frequency tables, and
surfaces **negative candidates** — n-grams with high cost and low / zero
conversions.

All amounts are in the configured account currency (AED for Talas).
``cost_micros / 1e6`` = AED.

READ-ONLY: only ``run_gaql`` is used.  Nothing here mutates the account.
Date window always ends YESTERDAY (never same-day — 24-48h attribution lag).
"""

import re
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta

import click

from ..ads import run_gaql
from ..output import print_table, print_json

# Arabic Unicode block range (U+0600 – U+06FF) plus extended Arabic ranges.
# The regex matches any word character (Latin/digit/underscore) plus Arabic-range codepoints.
_TOKEN_RE = re.compile(r"[\w؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]+")

# Detect whether a token contains Arabic script
_ARABIC_RE = re.compile(r"[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]")


def _window(days: int):
    """Return (d_from, d_to) as YYYY-MM-DD strings.  d_to = yesterday."""
    d_to = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    d_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return d_from, d_to


def _tokenize(term: str):
    """Return a list of cleaned tokens from a search term.

    Rules:
    - Lowercase Latin characters; Arabic script preserved as-is.
    - Strips punctuation but keeps characters in the Arabic Unicode range.
    - Drops pure-numeric tokens (e.g. "2024", "123").
    - Drops single-character tokens.
    """
    raw_tokens = _TOKEN_RE.findall(term.lower())
    tokens = []
    for tok in raw_tokens:
        # Drop pure-numeric tokens
        if tok.isdigit():
            continue
        # Drop single-character tokens (noise)
        if len(tok) <= 1:
            continue
        tokens.append(tok)
    return tokens


def _build_ngrams(tokens: list, max_n: int):
    """Yield all n-grams (1..max_n) from a token list as joined strings."""
    for n in range(1, max_n + 1):
        for i in range(len(tokens) - n + 1):
            yield n, " ".join(tokens[i : i + n])


def _lang(ngram: str) -> str:
    """Return 'ar' if the n-gram contains any Arabic codepoint, else 'en'."""
    return "ar" if _ARABIC_RE.search(ngram) else "en"


def analyze_ngrams(
    creds,
    days: int = 30,
    n: int = 3,
    min_cost: float = 1.0,
    top: int = 50,
) -> dict:
    """Cluster search terms into n-grams and surface negative candidates.

    Parameters
    ----------
    creds:      credentials object from ``gads_lib.get_credentials()``.
    days:       look-back window ending YESTERDAY (default 30).
    n:          maximum gram size — produces 1-grams through n-grams (default 3).
    min_cost:   minimum AED cost threshold for inclusion (default 1.0 AED).
    top:        maximum rows per gram-size bucket in the result (default 50).

    Returns
    -------
    {
        "window":  {"from": str, "to": str, "days": int},
        "currency": str,   # "AED"
        "ngrams": {
            "1": [{"ngram", "cost", "conv", "clicks", "impr", "terms", "cpa", "lang"}, ...],
            "2": [...],
            "3": [...],
            ...
        },
        "negative_candidates": [
            {"ngram", "n", "cost", "conv", "clicks", "terms", "lang", "reason"}, ...
        ],  # sorted desc by cost
    }
    """
    from ..config import CURRENCY

    d_from, d_to = _window(days)
    where_date = f"WHERE segments.date BETWEEN '{d_from}' AND '{d_to}'"

    # ── Fetch search terms from the API ──────────────────────────────────────
    rows = run_gaql(
        creds,
        f"""
        SELECT search_term_view.search_term,
               metrics.cost_micros,
               metrics.conversions,
               metrics.clicks,
               metrics.impressions
        FROM search_term_view
        {where_date}
        """,
    )

    # ── Aggregate metrics per search term (defensive: may appear in >1 adgroup) ─
    term_agg: dict = {}
    for r in rows:
        st = r.get("searchTermView", {})
        m = r.get("metrics", {})
        term = st.get("searchTerm", "").strip()
        if not term:
            continue
        cost = int(m.get("costMicros", 0)) / 1e6
        conv = float(m.get("conversions", 0))
        clicks = int(m.get("clicks", 0))
        impr = int(m.get("impressions", 0))
        agg = term_agg.setdefault(term, {"cost": 0.0, "conv": 0.0, "clicks": 0, "impr": 0})
        agg["cost"] += cost
        agg["conv"] += conv
        agg["clicks"] += clicks
        agg["impr"] += impr

    # ── Build n-gram accumulators ─────────────────────────────────────────────
    # Structure: {gram_size: {ngram_str: {cost, conv, clicks, impr, terms_set}}}
    ngram_agg: dict = defaultdict(lambda: defaultdict(
        lambda: {"cost": 0.0, "conv": 0.0, "clicks": 0, "impr": 0, "terms": set()}
    ))

    for term, agg in term_agg.items():
        tokens = _tokenize(term)
        if not tokens:
            continue
        seen_in_term: set = set()  # avoid double-counting the same ngram within a term
        for gram_n, gram in _build_ngrams(tokens, n):
            key = (gram_n, gram)
            if key in seen_in_term:
                continue
            seen_in_term.add(key)
            bucket = ngram_agg[gram_n][gram]
            bucket["cost"] += agg["cost"]
            bucket["conv"] += agg["conv"]
            bucket["clicks"] += agg["clicks"]
            bucket["impr"] += agg["impr"]
            bucket["terms"].add(term)

    # ── Serialise into sorted lists, one per gram size ───────────────────────
    result_ngrams: dict = {}
    for gram_n in sorted(ngram_agg.keys()):
        items = []
        for gram, b in ngram_agg[gram_n].items():
            cost = round(b["cost"], 2)
            if cost < min_cost:
                continue
            conv = round(b["conv"], 4)
            cpa = round(cost / conv, 2) if conv > 0 else None
            items.append({
                "ngram": gram,
                "cost": cost,
                "conv": conv,
                "clicks": b["clicks"],
                "impr": b["impr"],
                "terms": len(b["terms"]),
                "cpa": cpa,
                "lang": _lang(gram),
            })
        items.sort(key=lambda x: x["cost"], reverse=True)
        result_ngrams[str(gram_n)] = items[:top]

    # ── Negative candidates: high cost + zero/near-zero conversions ──────────
    # Strategy:
    #   - Primary: cost >= min_cost AND conv == 0          → "zero_conversions"
    #   - Secondary: cost >= min_cost*5 AND 0 < conv very low
    #     (CPA > 10× account average, if computable)         → "high_cpa"
    #
    # Compute account-average CPA from all aggregated search term data.
    total_cost_all = sum(b["cost"] for b in term_agg.values())
    total_conv_all = sum(b["conv"] for b in term_agg.values())
    acct_avg_cpa = (total_cost_all / total_conv_all) if total_conv_all > 0 else None

    neg_candidates = []
    for gram_n in sorted(ngram_agg.keys()):
        for gram, b in ngram_agg[gram_n].items():
            cost = round(b["cost"], 2)
            if cost < min_cost:
                continue
            conv = round(b["conv"], 4)
            reason = None
            if conv == 0:
                reason = "zero_conversions"
            elif acct_avg_cpa is not None:
                cpa = cost / conv
                # Flag if CPA is >= 5× the account average (aggressive negative signal)
                if cpa >= acct_avg_cpa * 5:
                    reason = f"high_cpa ({cpa:.2f} vs avg {acct_avg_cpa:.2f})"
            if reason:
                neg_candidates.append({
                    "ngram": gram,
                    "n": gram_n,
                    "cost": cost,
                    "conv": conv,
                    "clicks": b["clicks"],
                    "terms": len(b["terms"]),
                    "lang": _lang(gram),
                    "reason": reason,
                })

    neg_candidates.sort(key=lambda x: x["cost"], reverse=True)

    return {
        "window": {"from": d_from, "to": d_to, "days": days},
        "currency": CURRENCY,
        "ngrams": result_ngrams,
        "negative_candidates": neg_candidates,
    }


def render_ngrams(result: dict, as_json: bool = False, top: int = 25) -> None:
    """Render n-gram analysis to stdout.

    If ``as_json`` is True, print_json(result) and return.
    Otherwise render a rich terminal table per gram size plus a
    negative-candidates table.
    """
    if as_json:
        return print_json(result)

    w = result["window"]
    cur = result.get("currency", "AED")

    click.secho(
        f"\nN-gram search-term clustering — {w['from']} → {w['to']} ({w['days']}d)",
        fg="yellow",
        bold=True,
    )

    ngrams = result.get("ngrams", {})
    for gram_n_str in sorted(ngrams.keys(), key=int):
        gram_n = int(gram_n_str)
        label = {1: "Unigrams (1-grams)", 2: "Bigrams (2-grams)", 3: "Trigrams (3-grams)"}.get(
            gram_n, f"{gram_n}-grams"
        )
        items = ngrams[gram_n_str][:top]
        click.secho(f"\n{label}  [top {len(items)}, by {cur} cost]", fg="white", bold=True)
        if not items:
            click.echo("  (no data above min_cost threshold)")
            continue
        # Render cost/cpa as strings so print_table doesn't re-format them oddly
        display_rows = []
        for row in items:
            display_rows.append({
                "ngram": row["ngram"],
                "cost": f"{row['cost']:,.2f}",
                "conv": f"{row['conv']:,.2f}",
                "clicks": row["clicks"],
                "impr": row["impr"],
                "terms": row["terms"],
                "cpa": f"{row['cpa']:,.2f}" if row["cpa"] is not None else "—",
                "lang": row["lang"],
            })
        print_table(
            display_rows,
            ["ngram", "cost", "conv", "clicks", "impr", "terms", "cpa", "lang"],
        )

    neg = result.get("negative_candidates", [])[:top]
    click.secho(
        f"\nNegative candidates  [{len(neg)} shown, sorted by {cur} cost]",
        fg="red",
        bold=True,
    )
    if not neg:
        click.echo("  (none above threshold)")
    else:
        display_neg = []
        for row in neg:
            display_neg.append({
                "ngram": row["ngram"],
                "n": row["n"],
                "cost": f"{row['cost']:,.2f}",
                "conv": f"{row['conv']:,.2f}",
                "clicks": row["clicks"],
                "terms": row["terms"],
                "lang": row["lang"],
                "reason": row["reason"],
            })
        print_table(
            display_neg,
            ["ngram", "n", "cost", "conv", "clicks", "terms", "lang", "reason"],
        )

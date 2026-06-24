"""Landing-page conversion scoring for Talas branch landing pages.

Fetches the branch LP HTML and scores it 0-100 across six weighted dimensions:
  message_match, trust, mobile, load, cta, branch_param

READ-ONLY: only HTTP GETs are performed. Never touches the Google Ads account.
Network failures are caught and returned as {"error": "..."} — never raised.
"""

import re

import click
import requests

from ..output import print_table, print_json

# ---------------------------------------------------------------------------
# Branch URLs (canonical)
# ---------------------------------------------------------------------------

BRANCH_URLS: dict[str, str] = {
    "qz3":  "https://shop.talas.ae/pages/contact-talas?branch=qz3",
    "sja":  "https://shop.talas.ae/pages/contact-talas?branch=sja",
    "ind4": "https://shop.talas.ae/pages/contact-talas?branch=ind4",
}

# Branch phones (for trust subscore)
_BRANCH_PHONES: dict[str, str] = {
    "qz3":  "+971566662075",
    "sja":  "+971501996588",
    "ind4": "+971564045033",
}

# Branches that sell Korean parts (in addition to Tesla)
_KOREAN_BRANCHES = {"sja", "ind4"}

# Subscore weights (must sum to 100)
_WEIGHTS: dict[str, int] = {
    "message_match": 30,
    "trust":         20,
    "mobile":        15,
    "load":          15,
    "cta":           12,
    "branch_param":   8,
}

_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Individual subscore functions
# ---------------------------------------------------------------------------

def _score_message_match(html_lower: str, branch: str) -> tuple[float, list[str]]:
    """30 pts: does the page text mention Tesla (and Korean brands for ind4/sja)?"""
    issues = []
    pts = 0.0

    # Tesla is required for all branches
    if "tesla" in html_lower:
        pts += 20
    else:
        issues.append("Page text does not mention 'Tesla' — message mismatch for Tesla parts")

    if branch in _KOREAN_BRANCHES:
        # ind4 and sja also sell Korean parts
        korean_brands = ["kia", "hyundai", "genesis", "korean"]
        found = any(b in html_lower for b in korean_brands)
        if found:
            pts += 10
        else:
            issues.append(
                f"Branch {branch.upper()} sells Korean parts but page has no Korean brand mention "
                "(kia/hyundai/genesis)"
            )
    else:
        # qz3 is Tesla-only; reward that it does NOT mention Korean brands (no deduction either)
        pts += 10  # full points — no Korean requirement

    return min(pts, 30.0), issues


def _score_trust(html_lower: str, html_raw: str, branch: str, final_url: str) -> tuple[float, list[str]]:
    """20 pts: phone, address/location, business name 'Talas', HTTPS."""
    issues = []
    pts = 0.0

    # HTTPS (5 pts)
    if final_url.startswith("https://"):
        pts += 5
    else:
        issues.append("Final URL is not HTTPS — trust signal missing")

    # Business name 'Talas' (5 pts)
    if "talas" in html_lower:
        pts += 5
    else:
        issues.append("Business name 'Talas' not found in page text")

    # Phone number (5 pts)
    phone = _BRANCH_PHONES.get(branch, "")
    # normalise: remove spaces/dashes for fuzzy match
    phone_digits = re.sub(r"\D", "", phone)
    html_digits = re.sub(r"\D", "", html_raw)
    if phone_digits and phone_digits in html_digits:
        pts += 5
    else:
        issues.append(
            f"Branch phone {phone} not found in page — customers may not see the right contact"
        )

    # Address or location mention (5 pts) — look for common UAE address signals
    address_hints = ["al quoz", "quoz", "sharjah", "sajaa", "industrial", "dubai", "uae", "emirate"]
    if any(h in html_lower for h in address_hints):
        pts += 5
    else:
        issues.append("No location/address reference found on page (Dubai/Sharjah/UAE etc.)")

    return min(pts, 20.0), issues


def _score_mobile(html_lower: str) -> tuple[float, list[str]]:
    """15 pts: viewport meta, responsive CSS hints."""
    issues = []
    pts = 0.0

    if 'name="viewport"' in html_lower or "name='viewport'" in html_lower:
        pts += 10
    else:
        issues.append("Missing <meta name=\"viewport\"> — page may not be mobile-friendly")

    # Responsive hints: media queries or responsive framework classes
    responsive_hints = [
        "@media",
        "max-width",
        "min-width",
        "responsive",
        "bootstrap",
        "tailwind",
        "flex",
        "grid",
    ]
    if any(h in html_lower for h in responsive_hints):
        pts += 5
    else:
        issues.append("No responsive CSS hints found (@media, flex, grid, etc.)")

    return min(pts, 15.0), issues


def _score_load(html_raw: str) -> tuple[float, list[str]]:
    """15 pts: penalise large HTML and many blocking scripts/images."""
    issues = []
    pts = 15.0

    byte_count = len(html_raw.encode("utf-8", errors="replace"))
    if byte_count > 500_000:
        pts -= 5
        issues.append(
            f"HTML is large ({byte_count // 1024} KB) — may slow initial paint for mobile users"
        )
    elif byte_count > 200_000:
        pts -= 2
        issues.append(f"HTML is moderately large ({byte_count // 1024} KB)")

    # Count render-blocking <script> tags (non-async, non-defer, non-module)
    script_tags = re.findall(r"<script\b([^>]*)>", html_raw, re.IGNORECASE)
    blocking_scripts = [
        s for s in script_tags
        if "async" not in s.lower() and "defer" not in s.lower() and "type=\"module\"" not in s.lower()
    ]
    if len(blocking_scripts) > 10:
        pts -= 5
        issues.append(
            f"{len(blocking_scripts)} blocking <script> tags — consider async/defer for faster LCP"
        )
    elif len(blocking_scripts) > 5:
        pts -= 2
        issues.append(f"{len(blocking_scripts)} blocking <script> tags (moderate)")

    # Count <img> tags
    img_count = len(re.findall(r"<img\b", html_raw, re.IGNORECASE))
    if img_count > 20:
        pts -= 3
        issues.append(f"{img_count} <img> tags — ensure lazy-loading is used")

    return max(pts, 0.0), issues


def _score_cta(html_lower: str) -> tuple[float, list[str]]:
    """12 pts: WhatsApp / wa.me / click-to-chat link present."""
    issues = []

    cta_signals = ["wa.me", "whatsapp", "click-to-chat", "api.whatsapp"]
    if any(s in html_lower for s in cta_signals):
        return 12.0, []

    issues.append(
        "No WhatsApp CTA link (wa.me / whatsapp) found — primary conversion action may be missing"
    )
    return 0.0, issues


def _score_branch_param(requested_url: str, final_url: str) -> tuple[float, list[str]]:
    """8 pts: requested URL has ?branch= AND it survives in the final response URL."""
    issues = []
    pts = 0.0

    has_param_in_request = "branch=" in requested_url
    has_param_in_final = "branch=" in final_url

    if has_param_in_request:
        pts += 4
    else:
        issues.append("Requested URL is missing ?branch= parameter")

    if has_param_in_final:
        pts += 4
    else:
        issues.append(
            "?branch= parameter was stripped after redirect — branch routing may be broken"
        )

    return min(pts, 8.0), issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_landing_page(branch: str, url: str = None, timeout: int = 20) -> dict:
    """Fetch the landing page and score it 0-100.

    Args:
        branch: One of "qz3", "sja", "ind4".
        url:    Override URL (defaults to BRANCH_URLS[branch]).
        timeout: HTTP request timeout in seconds.

    Returns dict with keys:
        branch, url, final_url, http_status, score (int),
        subscores (dict), issues (list[str]), bytes (int), error (None|str)
    """
    branch = branch.lower().strip()
    requested_url = url or BRANCH_URLS.get(branch, "")

    base: dict = {
        "branch": branch,
        "url": requested_url,
        "final_url": requested_url,
        "http_status": None,
        "score": 0,
        "subscores": {
            "message_match": 0,
            "trust": 0,
            "mobile": 0,
            "load": 0,
            "cta": 0,
            "branch_param": 0,
        },
        "issues": [],
        "bytes": 0,
        "error": None,
    }

    if not requested_url:
        base["error"] = f"Unknown branch '{branch}' and no url provided"
        return base

    try:
        resp = requests.get(
            requested_url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": _BROWSER_UA},
        )
        base["http_status"] = resp.status_code
        base["final_url"] = resp.url

        if resp.status_code != 200:
            base["error"] = f"HTTP {resp.status_code}"
            base["issues"].append(f"Page returned HTTP {resp.status_code}")
            return base

        html_raw = resp.text
        html_lower = html_raw.lower()
        byte_count = len(resp.content)
        base["bytes"] = byte_count

    except requests.exceptions.Timeout:
        base["error"] = f"Request timed out after {timeout}s"
        base["issues"].append(base["error"])
        return base
    except requests.exceptions.ConnectionError as exc:
        base["error"] = f"Connection error: {exc}"
        base["issues"].append(base["error"])
        return base
    except requests.exceptions.RequestException as exc:
        base["error"] = f"Request failed: {exc}"
        base["issues"].append(base["error"])
        return base

    # Run subscorers
    all_issues: list[str] = []

    mm_pts, mm_issues = _score_message_match(html_lower, branch)
    all_issues.extend(mm_issues)

    trust_pts, trust_issues = _score_trust(html_lower, html_raw, branch, resp.url)
    all_issues.extend(trust_issues)

    mobile_pts, mobile_issues = _score_mobile(html_lower)
    all_issues.extend(mobile_issues)

    load_pts, load_issues = _score_load(html_raw)
    all_issues.extend(load_issues)

    cta_pts, cta_issues = _score_cta(html_lower)
    all_issues.extend(cta_issues)

    bp_pts, bp_issues = _score_branch_param(requested_url, resp.url)
    all_issues.extend(bp_issues)

    subscores = {
        "message_match": round(mm_pts, 1),
        "trust":         round(trust_pts, 1),
        "mobile":        round(mobile_pts, 1),
        "load":          round(load_pts, 1),
        "cta":           round(cta_pts, 1),
        "branch_param":  round(bp_pts, 1),
    }

    total = sum(subscores.values())

    base["score"] = int(round(total))
    base["subscores"] = subscores
    base["issues"] = all_issues

    return base


def render_lp_score(result: dict, as_json: bool = False) -> None:
    """Print the LP score result to stdout.

    If as_json=True, delegates to print_json. Otherwise uses click.echo
    + print_table for a readable terminal view.
    """
    if as_json:
        return print_json(result)

    branch = result.get("branch", "?").upper()
    score = result.get("score", 0)
    error = result.get("error")
    http_status = result.get("http_status")
    final_url = result.get("final_url", "")
    byte_count = result.get("bytes", 0)

    # Colour the score
    if score >= 80:
        score_fg = "green"
    elif score >= 55:
        score_fg = "yellow"
    else:
        score_fg = "red"

    click.echo()
    click.secho(
        f"LP Score — {branch}  |  {result.get('url', '')}",
        fg="cyan", bold=True,
    )
    click.echo(f"  Final URL : {final_url}")
    click.echo(f"  HTTP      : {http_status}   Size: {byte_count // 1024 if byte_count else 0} KB")

    if error:
        click.secho(f"  ERROR     : {error}", fg="red", bold=True)

    click.echo()
    click.secho(
        f"  Overall score: ",
        nl=False,
    )
    click.secho(f"{score}/100", fg=score_fg, bold=True)

    # Subscore table
    subscores = result.get("subscores", {})
    weights = _WEIGHTS
    rows = [
        {
            "dimension": k,
            "score": f"{v:.1f}",
            "max": str(weights.get(k, "?")),
        }
        for k, v in subscores.items()
    ]
    if rows:
        click.echo()
        print_table(rows, ["dimension", "score", "max"])

    # Issues
    issues = result.get("issues", [])
    if issues:
        click.echo()
        click.secho("  Issues:", fg="yellow", bold=True)
        for issue in issues:
            click.echo(f"    • {issue}")
    else:
        click.echo()
        click.secho("  No issues detected.", fg="green")

    click.echo()

import json
import re
import subprocess

import click

EXIT_CODES = {
    "OK": 0,
    "GENERAL": 1,
    "USAGE": 2,
    "AUTH": 3,
    "NOT_FOUND": 4,
    "API": 5,
    "VALIDATION": 6,
    "DB": 7,
}


def print_error(message, code="GENERAL", exit_code=None, as_json=False):
    """Print a structured error and return the numeric exit code."""
    numeric = exit_code if exit_code is not None else EXIT_CODES.get(code, 1)
    if as_json:
        click.echo(
            json.dumps({"error": {"code": code, "message": message, "exit_code": numeric}}),
            err=True,
        )
    else:
        click.secho(f"✗ {message}", fg="red", err=True)
    return numeric


def flatten(obj, prefix=""):
    """Flatten nested dict for table display."""
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.update(flatten(v, key))
            else:
                items[key] = v
    return items


def print_table(rows, columns=None):
    """Print rows as an aligned terminal table."""
    if not rows:
        click.echo("  (no results)")
        return
    if columns is None:
        columns = list(rows[0].keys())

    widths = {c: len(c) for c in columns}
    str_rows = []
    for row in rows:
        sr = {}
        for c in columns:
            val = row.get(c, "")
            if val is None:
                val = "—"
            elif isinstance(val, float):
                val = f"{val:,.2f}"
            else:
                val = str(val)
            sr[c] = val
            widths[c] = max(widths[c], len(val))
        str_rows.append(sr)

    header = "  ".join(c.ljust(widths[c]) for c in columns)
    click.secho(header, fg="cyan", bold=True)
    click.echo("  ".join("─" * widths[c] for c in columns))
    for sr in str_rows:
        click.echo("  ".join(sr[c].ljust(widths[c]) for c in columns))


def print_json(data):
    """Pretty-print JSON to stdout."""
    click.echo(json.dumps(data, indent=2, default=str))


def classify_api_error(status_code, response_text, url=""):
    """Classify an HTTP error response into a structured envelope.

    Returns a dict with keys: code, message, action, service, scope, url, project_id
    Returns None if the error does not match any known classification.
    """
    body = response_text or ""
    url_lower = (url or "").lower()

    # 1. API_NOT_ENABLED — 403 with SERVICE_DISABLED / has not been used / API not enabled
    if status_code == 403 and (
        "SERVICE_DISABLED" in body
        or "has not been used in project" in body
        or "API not enabled" in body
    ):
        # Extract service name (e.g. "merchantapi" from "merchantapi.googleapis.com")
        service = "unknown"
        svc_match = re.search(r'([\w\-]+)\.googleapis\.com', body)
        if svc_match:
            service = svc_match.group(1)

        # Extract project_id (number or alphanumeric slug after "project")
        project_id = None
        proj_match = re.search(r'project[/ =]+(\d+|[a-z][a-z0-9\-]+)', body, re.IGNORECASE)
        if proj_match:
            project_id = proj_match.group(1)

        console_url = f"https://console.cloud.google.com/apis/library/{service}.googleapis.com"
        return {
            "code": "API_NOT_ENABLED",
            "message": f"API not enabled: {service}.googleapis.com. Enable it in GCP Console.",
            "action": "run_gcloud",
            "service": service,
            "scope": None,
            "url": console_url,
            "project_id": project_id,
        }

    # 2. MERCHANT_NOT_REGISTERED — 401 with GCP_NOT_REGISTERED or merchant URL
    if status_code == 401 and (
        "GCP_NOT_REGISTERED" in body
        or ("merchant" in url_lower and status_code == 401)
    ):
        return {
            "code": "MERCHANT_NOT_REGISTERED",
            "message": "Merchant Center account is not registered as a Google API developer.",
            "action": "register_merchant",
            "service": None,
            "scope": None,
            "url": "https://developers.google.com/merchant/api/guides/quickstart/direct-api-calls#step_1_register_as_a_developer",
            "project_id": None,
        }

    # 3. INSUFFICIENT_SCOPE — 403 with INSUFFICIENT_AUTHENTICATION_SCOPES
    if status_code == 403 and (
        "INSUFFICIENT_AUTHENTICATION_SCOPES" in body
        or "Request had insufficient authentication scopes" in body
    ):
        # Determine missing scope from URL
        if "webmasters" in url_lower or "searchconsole" in url_lower:
            scope = "https://www.googleapis.com/auth/webmasters.readonly"
        elif "analytics" in url_lower:
            scope = "https://www.googleapis.com/auth/analytics.readonly"
        elif "merchant" in url_lower or "merchantapi" in url_lower:
            scope = "https://www.googleapis.com/auth/content"
        elif "mybusiness" in url_lower or "businessprofile" in url_lower:
            scope = "https://www.googleapis.com/auth/business.manage"
        elif "googleads" in url_lower or "adwords" in url_lower:
            scope = "https://www.googleapis.com/auth/adwords"
        elif "datamanager" in url_lower:
            scope = "https://www.googleapis.com/auth/datamanager"
        else:
            scope = "unknown (check kb/manifest.json)"

        return {
            "code": "INSUFFICIENT_SCOPE",
            "message": "OAuth token is missing a required scope.",
            "action": "regen_token",
            "service": None,
            "scope": scope,
            "url": "run: python generate_token.py",
            "project_id": None,
        }

    # 4. PERMISSION_DENIED — 403 with PERMISSION_DENIED / allowlist, or 429 quota exhausted
    if (status_code == 403 and (
        "PERMISSION_DENIED" in body
        or "allowlist" in body.lower()
    )) or (status_code == 429 and "quota" in body.lower() and '"0"' in body):
        if "mybusiness" in url_lower or "businessprofile" in url_lower:
            allowlist_url = "https://developers.google.com/my-business/content/prereqs"
        else:
            allowlist_url = "https://console.cloud.google.com/iam-admin/iam"

        return {
            "code": "PERMISSION_DENIED",
            "message": "Permission denied — you may need to request API access or allowlisting.",
            "action": "request_allowlist",
            "service": None,
            "scope": None,
            "url": allowlist_url,
            "project_id": None,
        }

    return None


def offer_gcloud_enable(service, project_id=None, yes=False):
    """Offer to enable a GCP API via gcloud.

    If yes is False, prompt the user interactively.
    Returns True on success, False if skipped or gcloud is unavailable.
    """
    console_url = f"https://console.cloud.google.com/apis/library/{service}.googleapis.com"

    if not yes:
        answer = input(
            f"Enable {service}.googleapis.com on project {project_id or '(default)'}? [y/N] "
        )
        if answer.strip().lower() not in ("y", "yes"):
            print(f"Enable manually: {console_url}")
            return False

    cmd = ["gcloud", "services", "enable", f"{service}.googleapis.com"]
    if project_id:
        cmd += ["--project", project_id]

    try:
        subprocess.run(cmd, check=True)
        print(f"✓ {service}.googleapis.com enabled.")
        return True
    except FileNotFoundError:
        print(f"gcloud not found. Enable manually: {console_url}")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"gcloud error: {exc}")
        return False

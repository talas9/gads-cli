import re
import click
import requests

from .config import API_VERSION, CUSTOMER_ID, DEV_TOKEN, LOGIN_CUSTOMER_ID


def get_ads_headers(creds):
    return {
        "Authorization": f"Bearer {creds.token}",
        "developer-token": DEV_TOKEN,
        "login-customer-id": LOGIN_CUSTOMER_ID,
        "Content-Type": "application/json",
    }


def sanitize_keyword(keyword):
    """Remove special characters and collapse whitespace.
    
    Removes: ! @ % , * '
    Collapses multiple spaces to single space.
    """
    # Remove special chars
    sanitized = re.sub(r'[!@%,*\']', '', keyword)
    # Collapse whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized


def run_gaql(creds, query):
    """Execute a GAQL query via the REST searchStream endpoint."""
    resp = requests.post(
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}/googleAds:searchStream",
        headers=get_ads_headers(creds),
        json={"query": query},
    )
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)

    results = []
    for batch in resp.json():
        results.extend(batch.get("results", []))
    return results


def ads_search(creds, query):
    """Execute a GAQL query via the REST search endpoint (paginated).
    
    Uses pageToken loop instead of searchStream.
    Returns list of all results across pages.
    """
    url = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}/googleAds:search"
    )
    headers = get_ads_headers(creds)
    results = []
    page_token = None
    
    while True:
        payload = {"query": query}
        if page_token:
            payload["pageToken"] = page_token
        
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            detail = resp.text[:800]
            click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
            raise SystemExit(1)
        
        data = resp.json()
        results.extend(data.get("results", []))
        
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    
    return results


def ads_mutate(creds, resource_path, operations):
    """Single-resource mutate operation.
    
    POST to /{resource_path}:mutate with {"operations": operations}
    Returns response JSON.
    """
    url = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}/{resource_path}:mutate"
    )
    headers = get_ads_headers(creds)
    payload = {"operations": operations}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)
    
    return resp.json()


def ads_batch_mutate(creds, mutate_operations):
    """Cross-resource batch mutate operation.
    
    POST to /googleAds:mutate with {"mutateOperations": mutate_operations}
    KEY: use "mutateOperations" NOT "operations"
    Returns response JSON.
    """
    url = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}/googleAds:mutate"
    )
    headers = get_ads_headers(creds)
    payload = {"mutateOperations": mutate_operations}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)
    
    return resp.json()


def ads_upload_click_conversions(creds, conversions, conversion_action_id):
    """Upload click conversions.
    
    POST to /customers/{CID}:uploadClickConversions
    Injects conversion_action_id into each conversion object.
    """
    url = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}:uploadClickConversions"
    )
    headers = get_ads_headers(creds)
    
    # Inject conversion_action_id into each conversion
    enriched_conversions = []
    for conv in conversions:
        enriched = dict(conv)
        enriched["conversionAction"] = conversion_action_id
        enriched_conversions.append(enriched)
    
    payload = {
        "conversions": enriched_conversions,
        "partialFailure": True,
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)
    
    return resp.json()


def generate_keyword_ideas(creds, keywords=None, url=None, language_id="1000", geo_ids=None):
    """Generate keyword ideas.
    
    POST to /customers/{CID}:generateKeywordIdeas
    Supports keywordSeed, urlSeed, or both.
    Sanitizes keywords before sending.
    """
    if not keywords and not url:
        click.secho("✗ Must provide either keywords or url", fg="red", err=True)
        raise SystemExit(1)
    
    url_endpoint = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}:generateKeywordIdeas"
    )
    headers = get_ads_headers(creds)
    
    payload = {}
    
    if keywords:
        # Sanitize keywords
        sanitized = [sanitize_keyword(kw) for kw in keywords]
        payload["keywordSeed"] = {"keywords": sanitized}
    
    if url:
        payload["urlSeed"] = {"url": url}
    
    # Add language and geo targeting
    payload["languageId"] = language_id
    if geo_ids:
        payload["geoTargetConstants"] = [{"resourceName": f"geoTargetConstants/{geo_id}"} for geo_id in geo_ids]
    
    resp = requests.post(url_endpoint, headers=headers, json=payload)
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)
    
    return resp.json()


def generate_keyword_forecast(creds, keywords, language_id="1000", geo_ids=None):
    """Generate keyword forecast metrics.
    
    POST to /customers/{CID}:generateKeywordForecastMetrics
    Sanitizes keywords before sending.
    """
    url_endpoint = (
        f"https://googleads.googleapis.com/{API_VERSION}"
        f"/customers/{CUSTOMER_ID}:generateKeywordForecastMetrics"
    )
    headers = get_ads_headers(creds)
    
    # Sanitize keywords
    sanitized_keywords = [sanitize_keyword(kw) for kw in keywords]
    
    payload = {
        "campaignToForecast": {
            "keywordPlanKeywords": [
                {"keyword": kw} for kw in sanitized_keywords
            ],
            "keywordPlanNetwork": "GOOGLE_SEARCH",
            "languageConstants": [f"languageConstants/{language_id}"],
        }
    }
    
    if geo_ids:
        payload["campaignToForecast"]["geoTargetConstants"] = [
            f"geoTargetConstants/{geo_id}" for geo_id in geo_ids
        ]
    
    resp = requests.post(url_endpoint, headers=headers, json=payload)
    if resp.status_code != 200:
        detail = resp.text[:800]
        click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
        raise SystemExit(1)
    
    return resp.json()


# ── Customer Match / Audience Upload ─────────────────────────

import csv
import hashlib
import time


def _sha256(val):
    """SHA-256 hash a string (stripped, encoded UTF-8)."""
    return hashlib.sha256(val.strip().encode("utf-8")).hexdigest()


def _is_valid_name(n):
    """Return True only if name looks like a real person name, not company/garbage."""
    if not n or not n.strip():
        return False
    n = n.strip()
    if len(n) > 30:
        return False
    if re.search(r'[*(),\[\]{}|/\\]', n):
        return False
    if re.search(r'\d', n):
        return False
    if len(n.split()) > 4:
        return False
    return True


def _normalize_phone(raw):
    """Normalize phone to E.164 format. Returns normalized string or None."""
    if not raw:
        return None
    raw = raw.strip()
    # Remove common prefixes/formatting
    raw = re.sub(r'[\s\-\.\(\)]', '', raw)
    if raw.startswith('00'):
        raw = '+' + raw[2:]
    elif raw.startswith('05') and len(raw) == 10:
        raw = '+971' + raw[1:]
    elif raw.startswith('5') and len(raw) == 9:
        raw = '+971' + raw
    elif raw.startswith('971') and not raw.startswith('+'):
        raw = '+' + raw
    elif not raw.startswith('+'):
        raw = '+' + raw
    # Must have + and at least 8 digits
    digits = re.sub(r'[^\d]', '', raw)
    if len(digits) < 8:
        return None
    return '+' + digits


def _build_user_op(phone=None, email=None, first_name=None, last_name=None, country=""):
    """Build one Customer Match userDataOperation with SHA-256 hashed identifiers."""
    ids = []
    if phone:
        normalized = _normalize_phone(phone)
        if normalized:
            ids.append({"hashedPhoneNumber": _sha256(normalized)})
    if email and "@" in email:
        ids.append({"hashedEmail": _sha256(email.strip().lower())})
    if _is_valid_name(first_name) and _is_valid_name(last_name):
        addr = {
            "hashedFirstName": _sha256(first_name.strip().lower()),
            "hashedLastName": _sha256(last_name.strip().lower()),
        }
        if country:
            addr["countryCode"] = country.strip().upper()
        ids.append({"addressInfo": addr})
    if not ids:
        return None
    return {"create": {"userIdentifiers": ids}}


def audience_find_list(creds, name):
    """Find a user list by name. Returns resource_name or None."""
    results = run_gaql(creds, f"SELECT user_list.resource_name FROM user_list WHERE user_list.name = '{name}'")
    if results:
        return results[0].get("userList", {}).get("resourceName")
    return None


def audience_create_list(creds, name, description="", life_span=540):
    """Create a CRM-based Customer Match user list."""
    op = {"create": {
        "name": name,
        "description": description,
        "membershipStatus": "OPEN",
        "membershipLifeSpan": life_span,
        "crmBasedUserList": {
            "uploadKeyType": "CONTACT_INFO",
            "dataSourceType": "FIRST_PARTY",
        },
    }}
    return ads_mutate(creds, "userLists", [op])


def audience_upload_csv(creds, list_resource_name, csv_path, batch_size=100, max_rows=None):
    """Upload a CSV file to a Customer Match list.

    CSV format: Phone,Email,First Name,Last Name,Country
    All PII is SHA-256 hashed before upload.
    Names are validated — garbage/company names are skipped (phone-only).
    Consent (adUserData + adPersonalization = GRANTED) is included.

    Returns: (job_resource_name, stats_dict)
    """
    headers = get_ads_headers(creds)
    base = f"https://googleads.googleapis.com/{API_VERSION}/customers/{CUSTOMER_ID}"

    # 1. Create offline user data job
    job_url = f"{base}/offlineUserDataJobs:create"
    job_payload = {"job": {
        "type": "CUSTOMER_MATCH_USER_LIST",
        "customerMatchUserListMetadata": {
            "userList": list_resource_name,
            "consent": {
                "adUserData": "GRANTED",
                "adPersonalization": "GRANTED",
            }
        }
    }}
    resp = requests.post(job_url, headers=headers, json=job_payload, timeout=120)
    if resp.status_code != 200:
        click.secho(f"✗ Create job failed: {resp.text[:500]}", fg="red", err=True)
        raise SystemExit(1)
    job_rn = resp.json()["resourceName"]
    click.echo(f"  Job created: {job_rn}")

    # 2. Read CSV and build operations
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig", errors="replace") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if max_rows and i >= max_rows:
                break
            op = _build_user_op(
                phone=row.get("Phone", ""),
                email=row.get("Email", ""),
                first_name=row.get("First Name", ""),
                last_name=row.get("Last Name", ""),
                country=row.get("Country", ""),
            )
            if op:
                rows.append(op)

    click.echo(f"  Rows: {len(rows)} valid operations from CSV")

    # 3. Upload in batches with retry
    add_url = f"https://googleads.googleapis.com/{API_VERSION}/{job_rn}:addOperations"
    uploaded = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        for attempt in range(5):
            resp = requests.post(
                add_url, headers=headers,
                json={"operations": batch, "enableWarnings": True},
                timeout=120,
            )
            if resp.status_code == 200:
                uploaded += len(batch)
                break
            elif resp.status_code == 429:
                delay = 10 * (attempt + 1)
                click.echo(f"  Rate limited — waiting {delay}s (attempt {attempt + 1}/5)")
                time.sleep(delay)
            else:
                click.secho(f"✗ Upload batch failed: {resp.text[:500]}", fg="red", err=True)
                raise SystemExit(1)
        else:
            click.secho("✗ Upload failed after 5 retries (429)", fg="red", err=True)
            raise SystemExit(1)

    click.echo(f"  Uploaded: {uploaded} operations in {(len(rows) + batch_size - 1) // batch_size} batches")

    # 4. Run the job
    run_url = f"https://googleads.googleapis.com/{API_VERSION}/{job_rn}:run"
    resp = requests.post(run_url, headers=headers, json={}, timeout=120)
    if resp.status_code != 200:
        click.secho(f"✗ Run job failed: {resp.text[:500]}", fg="red", err=True)
        raise SystemExit(1)

    stats = {"job": job_rn, "rows_uploaded": uploaded, "total_csv_ops": len(rows)}
    return job_rn, stats

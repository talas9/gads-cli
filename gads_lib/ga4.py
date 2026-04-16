import click
import requests

from .config import GA4_PROPERTY_ID
from .http import get_bearer_headers, request_json

GA4_DATA_BASE = "https://analyticsdata.googleapis.com/v1beta"
GA4_ADMIN_BASE = "https://analyticsadmin.googleapis.com/v1alpha"

VALID_COUNTING_METHODS = ("ONCE_PER_EVENT", "ONCE_PER_SESSION")


def _require_property():
    if not GA4_PROPERTY_ID:
        import click
        click.secho("✗ GOOGLE_GA4_PROPERTY_ID not set in .env", fg="red", err=True)
        raise SystemExit(1)
    return GA4_PROPERTY_ID


def ga4_get_metadata(creds, property_id=None):
    pid = property_id or _require_property()
    return request_json(
        "GET",
        f"{GA4_DATA_BASE}/properties/{pid}/metadata",
        headers=get_bearer_headers(creds),
    )


def ga4_run_report(creds, dimensions, metrics, date_ranges, property_id=None, limit=10000):
    pid = property_id or _require_property()
    body = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "dateRanges": date_ranges,
        "limit": limit,
    }
    return request_json(
        "POST",
        f"{GA4_DATA_BASE}/properties/{pid}:runReport",
        headers=get_bearer_headers(creds),
        json_body=body,
    )


def ga4_run_realtime_report(creds, dimensions, metrics, property_id=None):
    pid = property_id or _require_property()
    body = {
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
    }
    return request_json(
        "POST",
        f"{GA4_DATA_BASE}/properties/{pid}:runRealtimeReport",
        headers=get_bearer_headers(creds),
        json_body=body,
    )


# ── Admin API: Key Events ────────────────────────────────────
#
# Key Events are the GA4 successor to "conversions". Toggling an event to
# a key event needs the analytics.edit scope; listing is covered by
# analytics.readonly.
#
# API: https://developers.google.com/analytics/devguides/config/admin/v1


def _normalise_property(property_id):
    """Return the bare numeric property id, stripping any 'properties/' prefix."""
    pid = (property_id or _require_property()).strip()
    if pid.startswith("properties/"):
        pid = pid.split("/", 1)[1]
    if not pid.isdigit():
        raise SystemExit(
            f"GA4 property id must be numeric (or 'properties/<id>'), got: {pid!r}"
        )
    return pid


def _raise_for_admin_status(resp, action):
    """Translate GA4 Admin API failures into actionable errors.

    403 → scope likely missing, point user to generate_token.py.
    404 → property id wrong.
    """
    if resp.status_code == 403:
        raise SystemExit(
            f"403 Forbidden while {action}. The OAuth token almost certainly "
            "lacks the analytics.edit scope — re-run tools/generate_token.py "
            "(or gads-cli/generate_token.py) to refresh it, then retry."
        )
    if resp.status_code == 404:
        raise SystemExit(
            f"404 Not Found while {action}. Check GOOGLE_GA4_PROPERTY_ID — "
            "it must be the numeric GA4 property id (not a Measurement ID)."
        )
    if resp.status_code >= 400:
        raise SystemExit(
            f"GA4 Admin API error while {action} ({resp.status_code}): "
            f"{resp.text[:600]}"
        )


def list_key_events(property_id, creds):
    """Return all keyEvents on a GA4 property.

    Each item has keys: eventName, countingMethod, name (full resource path),
    plus createTime / custom flags from the API response.
    """
    pid = _normalise_property(property_id)
    url = f"{GA4_ADMIN_BASE}/properties/{pid}/keyEvents"
    items = []
    page_token = None
    while True:
        params = {"pageSize": 200}
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(url, headers=get_bearer_headers(creds), params=params, timeout=30)
        _raise_for_admin_status(resp, "listing keyEvents")
        data = resp.json() if resp.text else {}
        items.extend(data.get("keyEvents", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return items


def create_key_event(property_id, creds, event_name, counting_method="ONCE_PER_SESSION"):
    """Create (mark) an event as a key event. Idempotent.

    Returns the API response dict on success. If the event is already a key
    event (409 Conflict), returns the existing entry from a preceding list
    call so callers still get a well-formed dict.
    """
    if counting_method not in VALID_COUNTING_METHODS:
        raise ValueError(
            f"counting_method must be one of {VALID_COUNTING_METHODS}, got {counting_method!r}"
        )
    pid = _normalise_property(property_id)
    url = f"{GA4_ADMIN_BASE}/properties/{pid}/keyEvents"
    body = {"eventName": event_name, "countingMethod": counting_method}
    resp = requests.post(url, headers=get_bearer_headers(creds), json=body, timeout=30)
    if resp.status_code == 409:
        # Already exists — look it up from the list so we still return a dict.
        for existing in list_key_events(pid, creds):
            if existing.get("eventName") == event_name:
                existing = dict(existing)
                existing["_already_exists"] = True
                return existing
        return {"eventName": event_name, "countingMethod": counting_method, "_already_exists": True}
    _raise_for_admin_status(resp, f"creating keyEvent {event_name!r}")
    data = resp.json() if resp.text else {}
    data["_already_exists"] = False
    return data


def delete_key_event(property_id, creds, event_name):
    """Delete a keyEvent by event name. Returns True if deleted, False if not found."""
    pid = _normalise_property(property_id)
    target = None
    for existing in list_key_events(pid, creds):
        if existing.get("eventName") == event_name:
            target = existing
            break
    if target is None:
        return False
    resource_name = target.get("name")
    if not resource_name:
        raise SystemExit(
            f"keyEvent {event_name!r} found but has no resource name — cannot delete."
        )
    url = f"{GA4_ADMIN_BASE}/{resource_name}"
    resp = requests.delete(url, headers=get_bearer_headers(creds), timeout=30)
    if resp.status_code in (200, 204):
        return True
    _raise_for_admin_status(resp, f"deleting keyEvent {event_name!r}")
    return True  # unreachable — _raise_for_admin_status exits on any >=400

"""Google Data Manager API client.

API: Data Manager API
KB reference: kb/data-manager-api.md (relative to gads-cli root)
Official docs: https://developers.google.com/data-manager/api/reference/rest/v1

Unlike gads_lib/ads.py (Google Ads REST API), Data Manager calls need only a
bearer token -- no developer-token / login-customer-id HTTP headers. The MCC
"acting as" relationship is instead expressed inside the JSON body via the
Destination.loginAccount field (see _google_ads_destination() below).
"""
from .ads import _normalize_phone, _sha256
from .config import CUSTOMER_ID, LOGIN_CUSTOMER_ID
from .http import get_bearer_headers, request_json

DATAMANAGER_BASE_URL = "https://datamanager.googleapis.com/v1"

# Data Manager API hard limits (kb/data-manager-api.md § Quotas).
MAX_EVENTS_PER_REQUEST = 2000
MAX_AUDIENCE_MEMBERS_PER_REQUEST = 10000


def _google_ads_destination(product_destination_id):
    """Build a Google Ads `Destination` object for the configured account.

    operatingAccount is always the configured GOOGLE_ADS_CUSTOMER_ID. When
    GOOGLE_ADS_LOGIN_CUSTOMER_ID is set (MCC manager-access scenario), it is
    sent as loginAccount -- the Data Manager equivalent of the Ads REST API's
    `login-customer-id` header.
    """
    destination = {
        "operatingAccount": {"accountId": CUSTOMER_ID, "accountType": "GOOGLE_ADS"},
        "productDestinationId": product_destination_id,
    }
    if LOGIN_CUSTOMER_ID:
        destination["loginAccount"] = {"accountId": LOGIN_CUSTOMER_ID, "accountType": "GOOGLE_ADS"}
    return destination


def build_user_identifiers(phone=None, email=None):
    """Build a `UserData.userIdentifiers[]` list (SHA-256 hex hashed).

    Reuses the phone/email normalization already used by the legacy
    Customer Match path (gads_lib.ads._normalize_phone / _sha256).

    Data Manager's address-based identifier (AddressInfo) requires
    givenName + familyName + regionCode + postalCode (all required per the
    API reference) -- the CSV shape this CLI accepts for audience uploads
    (Phone/Email/First Name/Last Name/Country) carries no postal code, so
    address-based identifiers are intentionally not built here. Only phone
    and email identifiers are supported by this helper.

    Returns [] if neither a valid phone nor a valid email was supplied.
    """
    ids = []
    if phone:
        normalized = _normalize_phone(phone)
        if normalized:
            ids.append({"phoneNumber": _sha256(normalized)})
    if email and "@" in email:
        ids.append({"emailAddress": _sha256(email.strip().lower())})
    return ids


# KB: kb/data-manager-api.md § events-ingest | https://developers.google.com/data-manager/api/reference/rest/v1/events/ingest
def datamanager_ingest_events(creds, events, conversion_action_id, as_json=False):
    """Ingest a batch of conversion events via the Data Manager API.

    POST to /v1/events:ingest with a single Google Ads Destination built
    from conversion_action_id (the bare Google Ads conversion action ID --
    NOT a "customers/.../conversionActions/..." resource name -- becomes the
    Destination's productDestinationId, per the API's documented examples).

    Caller (the CLI layer) is responsible for chunking to <=2000 events per
    call -- this function does not chunk; it raises ValueError if handed
    more than MAX_EVENTS_PER_REQUEST events.

    The response is asynchronous: a 200 means the request was accepted, not
    that any individual event was successfully matched/recorded. It returns
    only {"requestId": "..."}; there is no per-event success/failure detail.
    """
    if len(events) > MAX_EVENTS_PER_REQUEST:
        raise ValueError(
            f"datamanager_ingest_events received {len(events)} events; "
            f"max {MAX_EVENTS_PER_REQUEST} per request. Chunk before calling."
        )
    url = f"{DATAMANAGER_BASE_URL}/events:ingest"
    headers = get_bearer_headers(creds)
    payload = {
        "destinations": [_google_ads_destination(conversion_action_id)],
        "events": events,
    }
    return request_json("POST", url, headers=headers, json_body=payload, as_json=as_json)


# KB: kb/data-manager-api.md § audiencemembers-ingest | https://developers.google.com/data-manager/api/reference/rest/v1/audienceMembers/ingest
def datamanager_ingest_audience_members(creds, members, destination_list_resource_name, as_json=False):
    """Ingest a batch of audience members via the Data Manager API.

    POST to /v1/audienceMembers:ingest with a single Google Ads Destination
    built from destination_list_resource_name (the bare Customer Match
    user-list ID -- becomes the Destination's productDestinationId).

    Caller is responsible for chunking to <=10000 members per call -- this
    function does not chunk; it raises ValueError if handed too many.

    The response is asynchronous: {"requestId": "..."} only, with no
    per-member match confirmation.
    """
    if len(members) > MAX_AUDIENCE_MEMBERS_PER_REQUEST:
        raise ValueError(
            f"datamanager_ingest_audience_members received {len(members)} members; "
            f"max {MAX_AUDIENCE_MEMBERS_PER_REQUEST} per request. Chunk before calling."
        )
    url = f"{DATAMANAGER_BASE_URL}/audienceMembers:ingest"
    headers = get_bearer_headers(creds)
    payload = {
        "destinations": [_google_ads_destination(destination_list_resource_name)],
        "audienceMembers": members,
    }
    return request_json("POST", url, headers=headers, json_body=payload, as_json=as_json)

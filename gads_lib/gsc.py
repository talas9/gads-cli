"""Google Search Console API functions."""
from .http import get_bearer_headers, request_json

GSC_BASE = "https://www.googleapis.com/webmasters/v3"
GSC_INSPECT_BASE = "https://searchconsole.googleapis.com/v1"


def gsc_list_sites(creds):
    """List all verified Search Console sites."""
    return request_json("GET", f"{GSC_BASE}/sites", headers=get_bearer_headers(creds))


def gsc_search_analytics(
    creds,
    site_url,
    start_date,
    end_date,
    dimensions=None,
    row_limit=25,
    search_type="web",
    start_row=0,
    data_state="final",
    dimension_filter_groups=None,
):
    """Query Search Console search analytics.

    site_url: the property URL (e.g. "https://shop.talas.ae/" or "sc-domain:talas.ae")
    start_date/end_date: "YYYY-MM-DD" strings
    dimensions: list of "query", "page", "device", "country", "date"
    start_row: offset for pagination (0-based)
    data_state: "final", "all", or "hourly_all"
    dimension_filter_groups: optional list of server-side filter group dicts
    """
    import urllib.parse
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "rowLimit": row_limit,
        "type": search_type,
        "startRow": start_row,
        "dataState": data_state,
    }
    if dimensions:
        body["dimensions"] = dimensions
    if dimension_filter_groups:
        body["dimensionFilterGroups"] = dimension_filter_groups

    encoded_url = urllib.parse.quote(site_url, safe="")
    return request_json(
        "POST",
        f"{GSC_BASE}/sites/{encoded_url}/searchAnalytics/query",
        headers=get_bearer_headers(creds),
        json_body=body,
    )


def gsc_list_sitemaps(creds, site_url, sitemap_index=None):
    """List sitemaps for a Search Console property.

    site_url: the property URL (must match verified property exactly)
    sitemap_index: optional sitemap index URL to filter by
    Returns raw API response with a "sitemap" key.
    """
    import urllib.parse
    encoded_url = urllib.parse.quote(site_url, safe="")
    url = f"{GSC_BASE}/sites/{encoded_url}/sitemaps"
    params = {}
    if sitemap_index is not None:
        params["sitemapIndex"] = sitemap_index
    return request_json(
        "GET",
        url,
        headers=get_bearer_headers(creds),
        params=params if params else None,
    )


def gsc_url_inspect(creds, inspection_url, site_url, language_code="en-US"):
    """Inspect a URL using the Search Console URL Inspection API.

    inspection_url: the URL to inspect
    site_url: the verified Search Console property (goes in JSON body, not URL path)
    language_code: BCP-47 language code for the response (default "en-US")
    Returns raw API response.
    """
    body = {
        "inspectionUrl": inspection_url,
        "siteUrl": site_url,
        "languageCode": language_code,
    }
    return request_json(
        "POST",
        f"{GSC_INSPECT_BASE}/urlInspection/index:inspect",
        headers=get_bearer_headers(creds),
        json_body=body,
    )

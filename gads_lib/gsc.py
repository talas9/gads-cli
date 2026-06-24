"""Google Search Console API functions.

API: Google Search Console Webmasters API v3 + URL Inspection API v1
KB reference: kb/search-console.md (relative to gads-cli root)
Official docs: https://developers.google.com/webmaster-tools/v1/api_reference_index
"""
from .http import get_bearer_headers, request_json

GSC_BASE = "https://www.googleapis.com/webmasters/v3"
GSC_INSPECT_BASE = "https://searchconsole.googleapis.com/v1"


# KB: kb/search-console.md § sites | https://developers.google.com/webmaster-tools/v1/sites/list
def gsc_list_sites(creds, as_json=False):
    """List all verified Search Console sites."""
    return request_json("GET", f"{GSC_BASE}/sites", headers=get_bearer_headers(creds), as_json=as_json)


# KB: kb/search-console.md § search-analytics | https://developers.google.com/webmaster-tools/v1/searchanalytics/query
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
    as_json=False,
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
        as_json=as_json,
    )


# KB: kb/search-console.md § sitemaps | https://developers.google.com/webmaster-tools/v1/sitemaps/list
def gsc_list_sitemaps(creds, site_url, sitemap_index=None, as_json=False):
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
        as_json=as_json,
    )


# KB: kb/search-console.md § url-inspection | https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
def gsc_url_inspect(creds, inspection_url, site_url, language_code="en-US", as_json=False):
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
        as_json=as_json,
    )

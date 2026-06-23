"""
Comprehensive offline pytest test suite for gads-cli.

ALL HTTP calls are mocked — no live API calls.
Run from the gads-cli root:
    cd /home/talas9/talas-ads/gads-cli && python -m pytest tests/ -v
"""

import json
import io
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

# ── Ensure conftest env stubs are loaded before any gads_lib import ────────────
# (conftest.py sets os.environ stubs; this file only imports after that runs)


# =============================================================================
# GROUP A — Request construction (unit tests with mocked HTTP)
# =============================================================================


class TestGA4RunReportRequestShape:
    """A — ga4_run_report posts the correct JSON body."""

    def test_ga4_run_report_request_shape(self, fake_creds):
        """ga4_run_report builds the expected JSON body with dimensions/metrics/dateRanges/limit."""
        from gads_lib.ga4 import ga4_run_report

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"rows": []}'
        fake_resp.json.return_value = {"rows": []}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            ga4_run_report(
                fake_creds,
                dimensions=["date", "country"],
                metrics=["sessions", "activeUsers"],
                date_ranges=[{"startDate": "7daysAgo", "endDate": "yesterday"}],
                property_id="271773771",
                limit=500,
            )

        assert mock_req.called, "requests.request was never called"
        _, kwargs = mock_req.call_args
        body = kwargs.get("json") or {}

        assert "dimensions" in body, "body missing 'dimensions'"
        assert "metrics" in body, "body missing 'metrics'"
        assert "dateRanges" in body, "body missing 'dateRanges'"
        assert "limit" in body, "body missing 'limit'"

        # Dimensions are wrapped as {name: ...} objects
        dim_names = [d["name"] for d in body["dimensions"]]
        assert "date" in dim_names
        assert "country" in dim_names

        metric_names = [m["name"] for m in body["metrics"]]
        assert "sessions" in metric_names
        assert "activeUsers" in metric_names

        assert body["limit"] == 500


class TestGA4KeyEventsUsesV1Beta:
    """A — list_key_events() hits the v1beta Admin API URL."""

    def test_ga4_key_events_list_uses_v1beta(self, fake_creds):
        """list_key_events uses analyticsadmin.googleapis.com/v1beta (not v1alpha)."""
        from gads_lib.ga4 import list_key_events

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"keyEvents": []}'
        fake_resp.json.return_value = {"keyEvents": []}

        with patch("requests.get", return_value=fake_resp) as mock_get:
            result = list_key_events("271773771", fake_creds)

        assert mock_get.called
        called_url = mock_get.call_args[0][0]  # first positional arg
        assert "v1beta" in called_url, f"URL should contain 'v1beta', got: {called_url}"
        assert "analyticsadmin.googleapis.com" in called_url
        assert "v1alpha" not in called_url, "URL should not use v1alpha"
        assert result == []


class TestGSCSearchAnalyticsIncludesStartRow:
    """A — gsc_search_analytics includes startRow in the POST body."""

    def test_gsc_search_analytics_includes_startrow(self, fake_creds):
        """gsc_search_analytics sends 'startRow' in its POST JSON body."""
        from gads_lib.gsc import gsc_search_analytics

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"rows": []}'
        fake_resp.json.return_value = {"rows": []}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            gsc_search_analytics(
                fake_creds,
                site_url="https://shop.talas.ae/",
                start_date="2026-06-01",
                end_date="2026-06-22",
                dimensions=["query"],
                row_limit=25,
                start_row=50,
            )

        assert mock_req.called
        _, kwargs = mock_req.call_args
        body = kwargs.get("json") or {}

        assert "startRow" in body, f"body missing 'startRow'; got keys: {list(body.keys())}"
        assert body["startRow"] == 50
        assert body["startDate"] == "2026-06-01"
        assert body["endDate"] == "2026-06-22"
        assert body["rowLimit"] == 25


class TestMerchantListProductsURL:
    """A — mc_list_products() hits merchantapi.googleapis.com/products/v1."""

    def test_merchant_list_products_url(self, fake_creds):
        """mc_list_products uses the Merchant API v1 products sub-API URL."""
        from gads_lib.merchant import mc_list_products

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"products": []}'
        fake_resp.json.return_value = {"products": []}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            mc_list_products(fake_creds, max_results=10)

        assert mock_req.called
        _, kwargs = mock_req.call_args
        # The URL is passed as the second positional arg to requests.request(method, url, ...)
        called_url = mock_req.call_args[0][1]

        assert "merchantapi.googleapis.com" in called_url, (
            f"URL should contain 'merchantapi.googleapis.com', got: {called_url}"
        )
        assert "products/v1" in called_url, (
            f"URL should contain 'products/v1', got: {called_url}"
        )


class TestGBPDailyMetricsURL:
    """A — gbp_daily_metrics() hits businessprofileperformance.googleapis.com."""

    def test_gbp_daily_metrics_url(self, fake_creds):
        """gbp_daily_metrics uses the GBP Performance API base URL."""
        from gads_lib.gbp import gbp_daily_metrics

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"timeSeries": {"datedValues": []}}'
        fake_resp.json.return_value = {"timeSeries": {"datedValues": []}}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            gbp_daily_metrics(
                fake_creds,
                location_name="locations/123456",
                metric="CALL_CLICKS",
                start_date=(2026, 6, 1),
                end_date=(2026, 6, 22),
            )

        assert mock_req.called
        called_url = mock_req.call_args[0][1]
        assert "businessprofileperformance.googleapis.com" in called_url, (
            f"URL should contain 'businessprofileperformance.googleapis.com', got: {called_url}"
        )


# =============================================================================
# GROUP B — --json output structure
# =============================================================================


class TestOutputFlatten:
    """B — flatten() returns a flat dict."""

    def test_output_flatten_dict_simple(self):
        """flatten({a: 1}) returns {"a": 1} (trivial case)."""
        from gads_lib.output import flatten

        result = flatten({"a": 1, "b": 2})
        assert result == {"a": 1, "b": 2}

    def test_output_flatten_dict_nested(self):
        """flatten({a: {b: {c: 3}}}) returns {"a.b.c": 3}."""
        from gads_lib.output import flatten

        nested = {"campaign": {"name": "Tesla Parts", "budget": {"amountMicros": 50000000}}}
        result = flatten(nested)
        assert "campaign.name" in result
        assert result["campaign.name"] == "Tesla Parts"
        assert "campaign.budget.amountMicros" in result
        assert result["campaign.budget.amountMicros"] == 50000000
        # No sub-dicts in output
        for v in result.values():
            assert not isinstance(v, dict), f"Expected flat value, got dict: {v}"

    def test_output_flatten_dict_with_prefix(self):
        """flatten with a prefix prepends it to all keys."""
        from gads_lib.output import flatten

        result = flatten({"x": 1}, prefix="top")
        assert "top.x" in result
        assert result["top.x"] == 1

    def test_output_flatten_non_dict_input(self):
        """flatten with non-dict input returns empty dict (graceful)."""
        from gads_lib.output import flatten

        result = flatten("not-a-dict")
        assert result == {}

    def test_output_flatten_lists_preserved(self):
        """flatten does not recurse into list values — keeps them as-is."""
        from gads_lib.output import flatten

        result = flatten({"tags": ["a", "b", "c"], "count": 3})
        assert result["tags"] == ["a", "b", "c"]
        assert result["count"] == 3


class TestPrintJsonProducesValidJson:
    """B — print_json([...]) emits valid, parseable JSON."""

    def test_print_json_produces_valid_json(self, capsys):
        """print_json([{"key": "val"}]) outputs JSON that json.loads parses cleanly."""
        from gads_lib.output import print_json

        payload = [{"key": "val", "num": 42}]
        print_json(payload)

        captured = capsys.readouterr()
        output = captured.out.strip()
        assert output, "print_json produced no output"

        parsed = json.loads(output)
        assert isinstance(parsed, list)
        assert len(parsed) == 1
        assert parsed[0]["key"] == "val"
        assert parsed[0]["num"] == 42

    def test_print_json_produces_valid_json_dict(self, capsys):
        """print_json({}) outputs valid JSON for a dict."""
        from gads_lib.output import print_json

        print_json({"status": "ok", "count": 0})
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["status"] == "ok"

    def test_print_json_handles_non_serializable_with_default_str(self, capsys):
        """print_json serializes non-JSON-native types via default=str."""
        from gads_lib.output import print_json
        from datetime import date

        print_json({"date": date(2026, 6, 22)})
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        # date becomes a string via default=str
        assert "2026" in parsed["date"]


# =============================================================================
# GROUP C — SELECT-only guard
# =============================================================================


class TestGAQLSelectOnlyGuard:
    """C — run_gaql passes SELECT queries and rejects non-SELECT (via API error)."""

    def test_gaql_select_only_accepted(self, fake_creds):
        """run_gaql with a SELECT query calls the searchStream endpoint."""
        from gads_lib.ads import run_gaql

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = [{"results": [{"campaign": {"name": "Test"}}]}]

        with patch("requests.post", return_value=fake_resp) as mock_post:
            result = run_gaql(fake_creds, "SELECT campaign.name FROM campaign LIMIT 1")

        assert mock_post.called
        called_url = mock_post.call_args[0][0]
        assert "searchStream" in called_url

        assert result == [{"campaign": {"name": "Test"}}]

    def test_ads_mutate_non_select_raises_on_api_error(self, fake_creds):
        """ads_mutate on a 4xx response raises SystemExit (gate via API error path)."""
        from gads_lib.ads import ads_mutate

        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = "Bad Request: invalid operation"

        with patch("requests.post", return_value=fake_resp):
            with pytest.raises(SystemExit):
                ads_mutate(fake_creds, "campaigns", [{"badOp": {}}])

    def test_run_gaql_raises_sysexit_on_api_error(self, fake_creds):
        """run_gaql raises SystemExit(1) when the API returns a non-200 status."""
        from gads_lib.ads import run_gaql

        fake_resp = MagicMock()
        fake_resp.status_code = 403
        fake_resp.text = "Forbidden"

        with patch("requests.post", return_value=fake_resp):
            with pytest.raises(SystemExit) as exc_info:
                run_gaql(fake_creds, "SELECT campaign.name FROM campaign")
        assert exc_info.value.code == 1


# =============================================================================
# GROUP D — Error envelope / request_json behavior
# =============================================================================


class TestRequestJsonErrorBehavior:
    """D — request_json raises SystemExit on 4xx (no error envelope returned)."""

    def test_request_json_raises_sysexit_on_4xx(self, fake_creds):
        """request_json raises SystemExit(5) on 400 — does NOT return an error dict."""
        from gads_lib.http import request_json

        fake_resp = MagicMock()
        fake_resp.status_code = 400
        fake_resp.text = '{"error": {"code": 400, "message": "Bad Request"}}'

        with patch("requests.request", return_value=fake_resp):
            with pytest.raises(SystemExit) as exc_info:
                request_json("GET", "https://example.com/api")
        assert exc_info.value.code == 5  # EXIT_CODES["API"]

    def test_request_json_raises_sysexit_on_403(self, fake_creds):
        """request_json raises SystemExit(1) on 403 Forbidden."""
        from gads_lib.http import request_json

        fake_resp = MagicMock()
        fake_resp.status_code = 403
        fake_resp.text = "Forbidden"

        with patch("requests.request", return_value=fake_resp):
            with pytest.raises(SystemExit):
                request_json("POST", "https://example.com/api", json_body={"q": 1})

    def test_request_json_returns_dict_on_200(self):
        """request_json returns parsed JSON dict on 200 success."""
        from gads_lib.http import request_json

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"result": "ok"}'
        fake_resp.json.return_value = {"result": "ok"}

        with patch("requests.request", return_value=fake_resp):
            result = request_json("GET", "https://example.com/api")

        assert result == {"result": "ok"}

    def test_request_json_returns_empty_dict_on_empty_body(self):
        """request_json returns {} when response body is empty (e.g. 204-like)."""
        from gads_lib.http import request_json

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = ""  # empty body

        with patch("requests.request", return_value=fake_resp):
            result = request_json("DELETE", "https://example.com/api/item/1")

        assert result == {}

    def test_request_json_passes_correct_method_and_url(self):
        """request_json forwards method and URL correctly to requests.request."""
        from gads_lib.http import request_json

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = "{}"
        fake_resp.json.return_value = {}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            request_json("POST", "https://api.example.com/v1/resource", json_body={"k": "v"})

        mock_req.assert_called_once()
        args = mock_req.call_args[0]
        assert args[0] == "POST"
        assert args[1] == "https://api.example.com/v1/resource"
        assert mock_req.call_args[1]["json"] == {"k": "v"}


# =============================================================================
# GROUP E — KB check
# =============================================================================


class TestKBManifestIsValidJSON:
    """E — kb/manifest.json is valid JSON with expected structure per entry."""

    def test_kb_manifest_json_is_valid(self):
        """Load kb/manifest.json and verify it's a non-empty list with required keys."""
        manifest_path = Path(__file__).resolve().parent.parent / "kb" / "manifest.json"
        assert manifest_path.exists(), f"manifest.json not found at {manifest_path}"

        with open(manifest_path) as f:
            data = json.load(f)

        assert isinstance(data, list), "manifest.json must be a JSON array"
        assert len(data) > 0, "manifest.json must have at least one entry"

        required_keys = {"api", "slug", "current_version", "base_url", "status", "kb_file"}
        for i, entry in enumerate(data):
            missing = required_keys - set(entry.keys())
            assert not missing, (
                f"manifest entry {i} (api={entry.get('api')!r}) "
                f"missing required keys: {missing}"
            )
            assert isinstance(entry["api"], str) and entry["api"], (
                f"entry {i}: 'api' must be a non-empty string"
            )
            assert isinstance(entry["slug"], str) and entry["slug"], (
                f"entry {i}: 'slug' must be a non-empty string"
            )
            assert isinstance(entry["current_version"], str) and entry["current_version"], (
                f"entry {i}: 'current_version' must be a non-empty string"
            )

    def test_kb_manifest_contains_expected_slugs(self):
        """manifest.json contains entries for all major APIs."""
        manifest_path = Path(__file__).resolve().parent.parent / "kb" / "manifest.json"
        with open(manifest_path) as f:
            data = json.load(f)

        slugs = {entry["slug"] for entry in data}
        expected_slugs = {"google-ads", "ga4", "gbp", "search-console", "merchant-api"}
        missing = expected_slugs - slugs
        assert not missing, f"manifest.json missing expected slugs: {missing}"


class TestKBCheckDriftNoFalsePositives:
    """E — check_drift() runs without error and returns structured results."""

    def test_kb_check_drift_returns_list(self):
        """check_drift() returns a list of result dicts without raising."""
        from gads_lib.kb import check_drift

        results = check_drift()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_kb_check_drift_result_structure(self):
        """Each check_drift() result has the expected keys."""
        from gads_lib.kb import check_drift

        results = check_drift()
        required_keys = {"api", "slug", "manifest_version", "code_version", "drift", "status"}
        for entry in results:
            missing = required_keys - set(entry.keys())
            assert not missing, f"check_drift entry missing keys: {missing}"
            assert entry["status"] in ("OK", "DRIFT"), (
                f"status must be 'OK' or 'DRIFT', got {entry['status']!r}"
            )
            assert isinstance(entry["drift"], bool)

    def test_kb_check_drift_exits_0_when_aligned(self):
        """Entries with no drift have status='OK' and drift=False (code matches manifest)."""
        from gads_lib.kb import check_drift

        results = check_drift()
        # Find entries we actually track in code (code_version != "n/a")
        tracked = [r for r in results if r["code_version"] != "n/a"]
        assert len(tracked) > 0, "Expected at least one tracked entry"

        # For GA4 (v1beta in code and manifest), expect no drift
        ga4_entries = [r for r in tracked if r["slug"] == "ga4"]
        for entry in ga4_entries:
            assert not entry["drift"], (
                f"Unexpected drift for {entry['api']}: "
                f"manifest={entry['manifest_version']!r}, code={entry['code_version']!r}"
            )

    def test_kb_normalize_version_strips_minor(self):
        """_normalize_version strips minor patch from 'v24.1' → 'v24'."""
        from gads_lib.kb import _normalize_version

        assert _normalize_version("v24.1") == "v24"
        assert _normalize_version("v24") == "v24"
        assert _normalize_version("v1beta") == "v1beta"
        assert _normalize_version("v1alpha") == "v1alpha"
        assert _normalize_version("v3") == "v3"


# =============================================================================
# GROUP F — Version
# =============================================================================


class TestVersion:
    """F — Package version assertions."""

    def test_version_exists(self):
        """gads_lib.__version__ is a non-empty string."""
        import gads_lib

        assert hasattr(gads_lib, "__version__"), "gads_lib missing __version__"
        assert isinstance(gads_lib.__version__, str)
        assert gads_lib.__version__, "__version__ is empty"

    def test_version_is_semver_format(self):
        """gads_lib.__version__ follows MAJOR.MINOR.PATCH format."""
        import gads_lib

        parts = gads_lib.__version__.split(".")
        assert len(parts) == 3, f"Expected MAJOR.MINOR.PATCH, got {gads_lib.__version__!r}"
        for part in parts:
            assert part.isdigit(), (
                f"Version part {part!r} is not numeric in {gads_lib.__version__!r}"
            )

    def test_version_is_3_8_0(self):
        """gads_lib.__version__ == '3.8.0' — EXPECTED TO FAIL until version bumped."""
        import gads_lib

        # This test intentionally fails at v3.7.0 to signal the pending version bump.
        assert gads_lib.__version__ == "3.8.0", (
            f"Expected version 3.8.0, got {gads_lib.__version__!r}. "
            "Bump __version__ in gads_lib/__init__.py when releasing v3.8.0."
        )


# =============================================================================
# Additional unit tests for core utility functions
# =============================================================================


class TestSanitizeKeyword:
    """Bonus — sanitize_keyword removes special chars and collapses whitespace."""

    def test_removes_special_chars(self):
        from gads_lib.ads import sanitize_keyword

        assert sanitize_keyword("tesla!parts") == "teslaparts"
        assert sanitize_keyword("buy@tesla") == "buytesla"
        assert sanitize_keyword("a,b") == "ab"
        assert sanitize_keyword("it's") == "its"
        assert sanitize_keyword("50% off") == "50 off"

    def test_collapses_whitespace(self):
        from gads_lib.ads import sanitize_keyword

        assert sanitize_keyword("tesla  parts   uae") == "tesla parts uae"

    def test_strips_leading_trailing_whitespace(self):
        from gads_lib.ads import sanitize_keyword

        assert sanitize_keyword("  tesla parts  ") == "tesla parts"

    def test_empty_string(self):
        from gads_lib.ads import sanitize_keyword

        assert sanitize_keyword("") == ""

    def test_clean_keyword_unchanged(self):
        from gads_lib.ads import sanitize_keyword

        assert sanitize_keyword("tesla parts uae") == "tesla parts uae"


class TestNormalizePhone:
    """Bonus — _normalize_phone converts UAE numbers to E.164."""

    def test_uae_mobile_05(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("0501234567") == "+971501234567"

    def test_uae_mobile_5_nine_digits(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("501234567") == "+971501234567"

    def test_international_plus(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("+971501234567") == "+971501234567"

    def test_double_zero_prefix(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("00971501234567") == "+971501234567"

    def test_short_number_returns_none(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("123") is None

    def test_empty_returns_none(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone("") is None

    def test_none_returns_none(self):
        from gads_lib.ads import _normalize_phone

        assert _normalize_phone(None) is None


class TestPrintError:
    """Bonus — print_error returns the correct numeric exit code."""

    def test_print_error_returns_numeric_code(self):
        from gads_lib.output import print_error

        code = print_error("something went wrong", code="GENERAL")
        assert code == 1

    def test_print_error_auth_code(self):
        from gads_lib.output import print_error

        code = print_error("auth failed", code="AUTH")
        assert code == 3

    def test_print_error_override_exit_code(self):
        from gads_lib.output import print_error

        code = print_error("custom error", exit_code=42)
        assert code == 42

    def test_print_error_json_mode(self, capsys):
        from gads_lib.output import print_error

        code = print_error("test message", code="AUTH", as_json=True)
        captured = capsys.readouterr()
        # JSON output goes to stderr
        parsed = json.loads(captured.err.strip())
        assert "error" in parsed
        assert parsed["error"]["code"] == "AUTH"
        assert "test message" in parsed["error"]["message"]
        assert code == 3


class TestGetBearerHeaders:
    """Bonus — get_bearer_headers builds Authorization: Bearer ... header."""

    def test_get_bearer_headers_structure(self, fake_creds):
        from gads_lib.http import get_bearer_headers

        headers = get_bearer_headers(fake_creds)
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer ya29.fake-access-token"
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"


class TestGSCBaseURL:
    """Bonus — GSC uses the correct webmasters/v3 base URL."""

    def test_gsc_list_sites_url(self, fake_creds):
        from gads_lib.gsc import gsc_list_sites

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"siteEntry": []}'
        fake_resp.json.return_value = {"siteEntry": []}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            gsc_list_sites(fake_creds)

        assert mock_req.called
        called_url = mock_req.call_args[0][1]
        assert "webmasters/v3" in called_url, f"Expected webmasters/v3 in URL, got: {called_url}"

    def test_gsc_search_analytics_url_encodes_site(self, fake_creds):
        """gsc_search_analytics URL-encodes the site_url in the path."""
        from gads_lib.gsc import gsc_search_analytics

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.text = '{"rows": []}'
        fake_resp.json.return_value = {"rows": []}

        with patch("requests.request", return_value=fake_resp) as mock_req:
            gsc_search_analytics(
                fake_creds,
                site_url="https://shop.talas.ae/",
                start_date="2026-06-01",
                end_date="2026-06-22",
            )

        called_url = mock_req.call_args[0][1]
        # The : and / in the site URL should be percent-encoded in the path
        assert "https%3A" in called_url or "https%3a" in called_url, (
            f"Expected URL-encoded site in path, got: {called_url}"
        )


class TestAdsSearchPagination:
    """Bonus — ads_search follows nextPageToken pagination."""

    def test_ads_search_single_page(self, fake_creds):
        """ads_search returns all results from a single-page response."""
        from gads_lib.ads import ads_search

        fake_resp = MagicMock()
        fake_resp.status_code = 200
        fake_resp.json.return_value = {
            "results": [{"campaign": {"name": "A"}}, {"campaign": {"name": "B"}}]
        }

        with patch("requests.post", return_value=fake_resp):
            results = ads_search(fake_creds, "SELECT campaign.name FROM campaign")

        assert len(results) == 2
        assert results[0]["campaign"]["name"] == "A"

    def test_ads_search_follows_next_page_token(self, fake_creds):
        """ads_search keeps paginating until nextPageToken is absent."""
        from gads_lib.ads import ads_search

        page1 = MagicMock()
        page1.status_code = 200
        page1.json.return_value = {
            "results": [{"campaign": {"name": "P1"}}],
            "nextPageToken": "tok123",
        }
        page2 = MagicMock()
        page2.status_code = 200
        page2.json.return_value = {
            "results": [{"campaign": {"name": "P2"}}],
            # no nextPageToken → stop
        }

        with patch("requests.post", side_effect=[page1, page2]):
            results = ads_search(fake_creds, "SELECT campaign.name FROM campaign")

        assert len(results) == 2
        assert results[0]["campaign"]["name"] == "P1"
        assert results[1]["campaign"]["name"] == "P2"


# =============================================================================
# GROUP G — Graceful API error handling
# =============================================================================


class TestGracefulErrorHandling:
    """Tests for classify_api_error() and offer_gcloud_enable()."""

    def test_api_not_enabled_403_service_disabled(self):
        """SERVICE_DISABLED → API_NOT_ENABLED classification."""
        from gads_lib.output import classify_api_error

        body = json.dumps({
            "error": {
                "code": 403,
                "status": "PERMISSION_DENIED",
                "message": (
                    "merchantapi.googleapis.com has not been used in project 123456789 before"
                    " or it is disabled. Enable it by visiting"
                    " https://console.cloud.google.com/apis/library/merchantapi.googleapis.com"
                    "?project=123456789"
                ),
                "details": [{
                    "@type": "type.googleapis.com/google.rpc.Help",
                    "links": [{"description": "Google APIs Console",
                               "url": "https://console.cloud.google.com/apis/library/"
                                      "merchantapi.googleapis.com?project=123456789"}]
                }]
            }
        })
        result = classify_api_error(
            403,
            body,
            url="https://merchantapi.googleapis.com/products/v1/accounts/123/products",
        )
        assert result is not None
        assert result["code"] == "API_NOT_ENABLED"
        assert result["action"] == "run_gcloud"
        assert "merchantapi" in result.get("service", "")

    def test_api_not_enabled_gcloud_present(self, monkeypatch):
        """When gcloud is present and user says yes, subprocess.run is called."""
        from gads_lib import output
        import subprocess

        inputs = iter(["y"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))

        run_calls = []

        def fake_run(cmd, **kwargs):
            run_calls.append(cmd)
            return MagicMock(returncode=0)

        monkeypatch.setattr(subprocess, "run", fake_run)
        result = output.offer_gcloud_enable("merchantapi", project_id="my-project", yes=False)
        assert result is True
        assert any("merchantapi.googleapis.com" in str(c) for c in run_calls)

    def test_api_not_enabled_gcloud_absent(self, monkeypatch, capsys):
        """When gcloud is absent (FileNotFoundError), falls back to console link."""
        from gads_lib import output
        import subprocess

        monkeypatch.setattr("builtins.input", lambda _: "y")

        def fake_run(cmd, **kwargs):
            raise FileNotFoundError("gcloud not found")

        monkeypatch.setattr(subprocess, "run", fake_run)
        result = output.offer_gcloud_enable("merchantapi", project_id="my-project", yes=False)
        assert result is False
        # Should print the console link fallback
        captured = capsys.readouterr()
        assert (
            "console.cloud.google.com" in captured.out
            or "console.cloud.google.com" in captured.err
        )

    def test_merchant_not_registered_401(self):
        """GCP_NOT_REGISTERED on merchant URL → MERCHANT_NOT_REGISTERED."""
        from gads_lib.output import classify_api_error

        body = json.dumps({
            "error": {"code": 401, "status": "UNAUTHENTICATED", "message": "GCP_NOT_REGISTERED"}
        })
        result = classify_api_error(
            401,
            body,
            url="https://merchantapi.googleapis.com/accounts/v1/accounts/123",
        )
        assert result is not None
        assert result["code"] == "MERCHANT_NOT_REGISTERED"
        assert result["action"] == "register_merchant"
        assert "developers.google.com/merchant" in result.get("url", "")

    def test_insufficient_scope_403_names_scope(self):
        """INSUFFICIENT_AUTHENTICATION_SCOPES on GSC URL → INSUFFICIENT_SCOPE with webmasters scope."""
        from gads_lib.output import classify_api_error

        body = json.dumps({
            "error": {
                "code": 403,
                "status": "PERMISSION_DENIED",
                "message": "Request had insufficient authentication scopes.",
            }
        })
        result = classify_api_error(
            403,
            body,
            url="https://www.googleapis.com/webmasters/v3/sites",
        )
        assert result is not None
        assert result["code"] == "INSUFFICIENT_SCOPE"
        assert result["action"] == "regen_token"
        assert "webmasters" in result.get("scope", "")

    def test_permission_denied_gbp_allowlist(self):
        """PERMISSION_DENIED on GBP URL → PERMISSION_DENIED with allowlist link."""
        from gads_lib.output import classify_api_error

        body = json.dumps({
            "error": {
                "code": 403,
                "status": "PERMISSION_DENIED",
                "message": "The caller does not have permission",
            }
        })
        result = classify_api_error(
            403,
            body,
            url="https://mybusinessbusinessinformation.googleapis.com/v1/accounts/123/locations",
        )
        assert result is not None
        assert result["code"] == "PERMISSION_DENIED"
        assert result["action"] == "request_allowlist"

    def test_request_json_exits_with_api_code_on_classified_error(self, monkeypatch):
        """request_json raises SystemExit(5) on a classified API error."""
        from gads_lib import http

        fake_resp = MagicMock()
        fake_resp.status_code = 403
        fake_resp.text = json.dumps({
            "error": {
                "message": "Request had insufficient authentication scopes.",
                "status": "PERMISSION_DENIED",
            }
        })
        monkeypatch.setattr("builtins.input", lambda _: "n")

        with patch("requests.request", return_value=fake_resp):
            with pytest.raises(SystemExit) as exc_info:
                http.request_json(
                    "GET",
                    "https://www.googleapis.com/webmasters/v3/sites",
                    headers={},
                )
        assert exc_info.value.code == 5  # EXIT_CODES["API"]

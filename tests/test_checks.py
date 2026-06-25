"""Offline pytest tests for gads_lib/analyze/checks.py.

ALL Google Ads API calls (run_gaql) are mocked.  No live HTTP.  No live DB.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Mock data helpers
# ---------------------------------------------------------------------------

def _rsa_row(ad_id, campaign, headlines, descriptions=None, impressions=100):
    if descriptions is None:
        descriptions = ["Buy Tesla Parts UAE — New Used Aftermarket available"]
    return {
        "adGroupAd": {
            "ad": {
                "id": ad_id,
                "responsiveSearchAd": {
                    "headlines": [{"text": h} for h in headlines],
                    "descriptions": [{"text": d} for d in descriptions],
                },
            },
            "adStrength": "GOOD",
            "status": "ENABLED",
        },
        "campaign": {"name": campaign},
        "adGroup": {"name": "AdGroup-1"},
        "metrics": {"impressions": impressions},
    }


def _camp_row(name, status="ENABLED"):
    return {"campaign": {"name": name, "status": status}, "metrics": {}}


def _conv_row(name, model="DATA_DRIVEN", category="DEFAULT"):
    return {
        "conversionAction": {
            "name": name,
            "status": "ENABLED",
            "countingType": "MANY_PER_CLICK",
            "category": category,
            "attributionModelSettings": {"attributionModel": model},
        }
    }


def _schedule_row(camp_name):
    return {
        "campaign": {"name": camp_name, "status": "ENABLED"},
        "campaignCriterion": {
            "type": "AD_SCHEDULE",
            "adSchedule": {"dayOfWeek": "MONDAY", "startHour": 9},
        },
    }


def _qs_row(kw_text, qs=7, post_click="ABOVE_AVERAGE", creative="AVERAGE",
            predicted_ctr="ABOVE_AVERAGE"):
    return {
        "adGroupCriterion": {
            "keyword": {"text": kw_text},
            "qualityInfo": {
                "qualityScore": qs,
                "postClickQualityScore": post_click,
                "creativeQualityScore": creative,
                "searchPredictedCtr": predicted_ctr,
            },
        },
        "metrics": {"impressions": 100},
    }


# ---------------------------------------------------------------------------
# 1. TestCheckRsaLengths
# ---------------------------------------------------------------------------

class TestCheckRsaLengths:
    """Tests for check_rsa_lengths — flags headlines < 20 chars or desc < 60 chars."""

    def test_short_headlines_detected(self, fake_creds):
        """Headline < 20 chars is flagged with HIGH impact when > 25% are short."""
        from gads_lib.analyze.checks import check_rsa_lengths

        # 3 headlines — all short (< 20 chars) → 100% short > 25% → HIGH
        rows = [_rsa_row("1", "Camp-A", ["Short", "Tiny", "Brief"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_lengths(fake_creds, days=30)

        assert result["impact"] == "HIGH"
        assert result["short_headlines"] != []
        assert all(item["length"] < 20 for item in result["short_headlines"])

    def test_short_descriptions_detected(self, fake_creds):
        """Description < 60 chars is flagged; impact HIGH when > 25% are short."""
        from gads_lib.analyze.checks import check_rsa_lengths

        short_desc = "Too short"  # well under 60 chars
        rows = [_rsa_row("1", "Camp-A", ["A" * 25], descriptions=[short_desc])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_lengths(fake_creds, days=30)

        assert result["short_descriptions"] != []
        assert result["short_descriptions"][0]["length"] < 60
        assert result["impact"] == "HIGH"

    def test_all_within_range_returns_info(self, fake_creds):
        """Long-enough copy → impact INFO, zero short counts."""
        from gads_lib.analyze.checks import check_rsa_lengths

        # headlines all ≥ 20, description ≥ 60
        headlines = ["Buy Tesla Parts UAE Now", "Fast UAE Delivery Available"]
        desc = "Shop new, used and aftermarket Tesla auto body parts at Talas UAE online."
        rows = [_rsa_row("1", "Camp-A", headlines, descriptions=[desc])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_lengths(fake_creds, days=30)

        assert result["impact"] == "INFO"
        assert result["short_headlines"] == []
        assert result["short_descriptions"] == []

    def test_empty_response_no_crash(self, fake_creds):
        """run_gaql returning [] produces zero counts and does not crash."""
        from gads_lib.analyze.checks import check_rsa_lengths

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_rsa_lengths(fake_creds, days=30)

        assert result["total_ads"] == 0
        assert result["total_headlines"] == 0
        assert result["total_descriptions"] == 0
        assert result["short_headlines"] == []
        assert result["short_descriptions"] == []

    def test_return_shape_has_required_keys(self, fake_creds):
        """Result contains all documented keys."""
        from gads_lib.analyze.checks import check_rsa_lengths

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_rsa_lengths(fake_creds, days=30)

        for key in (
            "window", "currency", "total_ads", "total_headlines", "total_descriptions",
            "short_headlines", "short_descriptions", "pct_headlines_short",
            "pct_descriptions_short", "impact",
        ):
            assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 2. TestCheckRsaDuplicates
# ---------------------------------------------------------------------------

class TestCheckRsaDuplicates:
    """Tests for check_rsa_duplicates — same headline text twice in one ad."""

    def test_duplicate_headline_detected(self, fake_creds):
        """Same headline text twice in one ad → ads_with_duplicates non-empty, impact HIGH."""
        from gads_lib.analyze.checks import check_rsa_duplicates

        rows = [_rsa_row("1", "Camp-A", ["Tesla Parts UAE", "Tesla Parts UAE", "Buy Now"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_duplicates(fake_creds, days=30)

        assert result["impact"] == "HIGH"
        assert result["count_affected"] == 1
        assert len(result["ads_with_duplicates"]) == 1
        assert "tesla parts uae" in result["ads_with_duplicates"][0]["duplicate_headlines"]

    def test_case_insensitive_match(self, fake_creds):
        """'Tesla Parts' and 'tesla parts' are treated as duplicates."""
        from gads_lib.analyze.checks import check_rsa_duplicates

        rows = [_rsa_row("2", "Camp-A", ["Tesla Parts", "tesla parts", "Fast Delivery UAE"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_duplicates(fake_creds, days=30)

        assert result["count_affected"] == 1
        assert result["impact"] == "HIGH"

    def test_no_duplicates_returns_info(self, fake_creds):
        """Unique headlines → impact INFO, count 0."""
        from gads_lib.analyze.checks import check_rsa_duplicates

        rows = [_rsa_row("3", "Camp-A", ["Tesla Parts UAE", "Buy Now Online", "Fast Delivery"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_rsa_duplicates(fake_creds, days=30)

        assert result["impact"] == "INFO"
        assert result["count_affected"] == 0
        assert result["ads_with_duplicates"] == []

    def test_empty_response_no_crash(self, fake_creds):
        """run_gaql returning [] → no crash, zero counts."""
        from gads_lib.analyze.checks import check_rsa_duplicates

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_rsa_duplicates(fake_creds, days=30)

        assert result["total_ads"] == 0
        assert result["count_affected"] == 0
        assert result["impact"] == "INFO"


# ---------------------------------------------------------------------------
# 3. TestCheckDkiPresence
# ---------------------------------------------------------------------------

class TestCheckDkiPresence:
    """Tests for check_dki_presence — Dynamic Keyword Insertion usage."""

    def test_dki_found_returns_true(self, fake_creds):
        """Ad with {keyword:...} → dki_found True, impact INFO."""
        from gads_lib.analyze.checks import check_dki_presence

        rows = [_rsa_row("1", "Camp-A", ["{keyword:Tesla Parts} UAE", "Fast Delivery"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_dki_presence(fake_creds, days=30)

        assert result["dki_found"] is True
        assert result["impact"] == "INFO"
        assert len(result["ads_with_dki"]) >= 1

    def test_no_dki_returns_medium(self, fake_creds):
        """No DKI ads → dki_found False, impact MEDIUM."""
        from gads_lib.analyze.checks import check_dki_presence

        rows = [_rsa_row("1", "Camp-A", ["Tesla Parts UAE", "Buy Online Now"])]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_dki_presence(fake_creds, days=30)

        assert result["dki_found"] is False
        assert result["impact"] == "MEDIUM"
        assert result["ads_with_dki"] == []

    def test_empty_response_no_crash(self, fake_creds):
        """run_gaql returning [] → no crash, dki_found False."""
        from gads_lib.analyze.checks import check_dki_presence

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_dki_presence(fake_creds, days=30)

        assert result["dki_found"] is False
        assert result["total_ads_checked"] == 0
        assert result["ads_with_dki"] == []

    def test_dki_case_insensitive(self, fake_creds):
        """{KEYWORD:...} and {Keyword:...} also match the DKI regex."""
        from gads_lib.analyze.checks import check_dki_presence

        rows = [
            _rsa_row("1", "Camp-A", ["{KEYWORD:Tesla} UAE", "Fast Delivery"]),
            _rsa_row("2", "Camp-B", ["{Keyword:Auto Parts} UAE", "Shop Now"]),
        ]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_dki_presence(fake_creds, days=30)

        assert result["dki_found"] is True
        assert len(result["ads_with_dki"]) == 2


# ---------------------------------------------------------------------------
# 4. TestCheckAdSchedule
# ---------------------------------------------------------------------------

class TestCheckAdSchedule:
    """Tests for check_ad_schedule — coverage of ad-schedule criteria."""

    def _side_effect_for(self, camp_rows, sched_rows):
        """Return a side_effect callable that routes by query content."""
        def _se(creds, query):
            q = query.upper()
            if "FROM CAMPAIGN\n" in q or "FROM CAMPAIGN " in q or "FROM CAMPAIGN\r" in q:
                # The active campaigns query hits campaign resource
                return camp_rows
            if "FROM CAMPAIGN_CRITERION" in q:
                return sched_rows
            return []
        return _se

    def test_all_scheduled_returns_info(self, fake_creds):
        """All campaigns have schedule → impact INFO, 100% coverage."""
        from gads_lib.analyze.checks import check_ad_schedule

        camp_rows = [_camp_row("Camp-A"), _camp_row("Camp-B")]
        sched_rows = [_schedule_row("Camp-A"), _schedule_row("Camp-B")]
        with patch(
            "gads_lib.analyze.checks.run_gaql",
            side_effect=self._side_effect_for(camp_rows, sched_rows),
        ):
            result = check_ad_schedule(fake_creds, days=30)

        assert result["impact"] == "INFO"
        assert result["coverage_pct"] == pytest.approx(100.0)
        assert result["unscheduled_campaigns"] == []

    def test_no_schedule_returns_high(self, fake_creds):
        """Campaigns exist but no schedules → impact HIGH."""
        from gads_lib.analyze.checks import check_ad_schedule

        camp_rows = [_camp_row("Camp-A"), _camp_row("Camp-B")]
        # No schedule rows at all
        with patch(
            "gads_lib.analyze.checks.run_gaql",
            side_effect=self._side_effect_for(camp_rows, []),
        ):
            result = check_ad_schedule(fake_creds, days=30)

        # 0% coverage < 50% → HIGH
        assert result["impact"] == "HIGH"
        assert result["coverage_pct"] == pytest.approx(0.0)
        assert set(result["unscheduled_campaigns"]) == {"Camp-A", "Camp-B"}

    def test_partial_coverage_returns_medium(self, fake_creds):
        """Some scheduled → impact MEDIUM (coverage 50 < x < 100)."""
        from gads_lib.analyze.checks import check_ad_schedule

        camp_rows = [_camp_row("Camp-A"), _camp_row("Camp-B")]
        sched_rows = [_schedule_row("Camp-A")]  # only Camp-A scheduled
        with patch(
            "gads_lib.analyze.checks.run_gaql",
            side_effect=self._side_effect_for(camp_rows, sched_rows),
        ):
            result = check_ad_schedule(fake_creds, days=30)

        assert result["impact"] == "MEDIUM"
        assert result["coverage_pct"] == pytest.approx(50.0)
        assert "Camp-B" in result["unscheduled_campaigns"]

    def test_empty_response_no_crash(self, fake_creds):
        """Both queries return [] → no crash, 100% coverage (vacuously true)."""
        from gads_lib.analyze.checks import check_ad_schedule

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_ad_schedule(fake_creds, days=30)

        assert result["total_search_campaigns"] == 0
        assert result["coverage_pct"] == pytest.approx(100.0)
        assert result["impact"] == "INFO"


# ---------------------------------------------------------------------------
# 5. TestCheckAttributionModel
# ---------------------------------------------------------------------------

class TestCheckAttributionModel:
    """Tests for check_attribution_model — flag LAST_CLICK conversion actions."""

    def test_last_click_flagged_high(self, fake_creds):
        """LAST_CLICK actions → impact HIGH."""
        from gads_lib.analyze.checks import check_attribution_model

        rows = [_conv_row("WhatsApp Click", model="LAST_CLICK")]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_attribution_model(fake_creds)

        assert result["impact"] == "HIGH"
        assert len(result["last_click_actions"]) == 1
        assert result["last_click_actions"][0]["name"] == "WhatsApp Click"

    def test_data_driven_returns_info(self, fake_creds):
        """DATA_DRIVEN only → impact INFO."""
        from gads_lib.analyze.checks import check_attribution_model

        rows = [
            _conv_row("Purchase", model="DATA_DRIVEN"),
            _conv_row("Lead", model="DATA_DRIVEN"),
        ]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_attribution_model(fake_creds)

        assert result["impact"] == "INFO"
        assert result["last_click_actions"] == []
        assert len(result["data_driven_actions"]) == 2

    def test_no_conversions_returns_info(self, fake_creds):
        """Empty response → zero total, impact INFO."""
        from gads_lib.analyze.checks import check_attribution_model

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_attribution_model(fake_creds)

        assert result["total_conversion_actions"] == 0
        assert result["impact"] == "INFO"

    def test_return_shape(self, fake_creds):
        """Result has last_click_actions, data_driven_actions, total_conversion_actions."""
        from gads_lib.analyze.checks import check_attribution_model

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_attribution_model(fake_creds)

        for key in ("last_click_actions", "data_driven_actions", "total_conversion_actions",
                    "other_actions", "impact", "recommendation"):
            assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# 6. TestCheckBudgetLostIs
# ---------------------------------------------------------------------------

class TestCheckBudgetLostIs:
    """Tests for check_budget_lost_is — search budget lost impression share > 10%."""

    def _budget_row(self, name, budget_lost):
        return {
            "campaign": {"name": name, "status": "ENABLED"},
            "metrics": {"searchBudgetLostImpressionShare": budget_lost},
        }

    def test_high_budget_lost_flagged(self, fake_creds):
        """30% budget lost IS → flagged, impact HIGH (avg > 20%)."""
        from gads_lib.analyze.checks import check_budget_lost_is

        rows = [self._budget_row("Camp-A", 0.30)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_budget_lost_is(fake_creds, days=30)

        assert result["impact"] == "HIGH"
        assert result["flagged_count"] >= 1
        assert result["avg_budget_lost_is_pct"] == pytest.approx(30.0, abs=0.1)

    def test_low_budget_lost_info(self, fake_creds):
        """5% budget lost IS → impact INFO."""
        from gads_lib.analyze.checks import check_budget_lost_is

        rows = [self._budget_row("Camp-A", 0.05)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_budget_lost_is(fake_creds, days=30)

        assert result["impact"] == "INFO"
        assert result["flagged_count"] == 0

    def test_sentinel_value_excluded(self, fake_creds):
        """Values > 1.5 (API sentinel for 'data unavailable') are excluded; no crash."""
        from gads_lib.analyze.checks import check_budget_lost_is

        rows = [self._budget_row("Camp-A", 9.22337203685478e+18)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_budget_lost_is(fake_creds, days=30)

        # Sentinel excluded → no valid data → avg is None → impact INFO
        assert result["avg_budget_lost_is_pct"] is None
        assert result["impact"] == "INFO"

    def test_empty_response_no_crash(self, fake_creds):
        """run_gaql returning [] → no crash, avg is None."""
        from gads_lib.analyze.checks import check_budget_lost_is

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_budget_lost_is(fake_creds, days=30)

        assert result["campaigns"] == []
        assert result["avg_budget_lost_is_pct"] is None
        assert result["flagged_count"] == 0

    def test_flagged_count_correct(self, fake_creds):
        """Campaigns > 10% are counted in flagged_count."""
        from gads_lib.analyze.checks import check_budget_lost_is

        rows = [
            self._budget_row("Camp-A", 0.15),   # 15% → flagged
            self._budget_row("Camp-B", 0.25),   # 25% → flagged
            self._budget_row("Camp-C", 0.05),   # 5%  → not flagged
        ]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_budget_lost_is(fake_creds, days=30)

        assert result["flagged_count"] == 2


# ---------------------------------------------------------------------------
# 7. TestCheckQsDistribution
# ---------------------------------------------------------------------------

class TestCheckQsDistribution:
    """Tests for check_qs_distribution — keyword QS band distribution."""

    def test_high_qs_returns_info(self, fake_creds):
        """Avg QS ≥ 7 → impact INFO."""
        from gads_lib.analyze.checks import check_qs_distribution

        rows = [_qs_row("tesla parts", qs=8), _qs_row("tesla bumper", qs=9)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_qs_distribution(fake_creds, days=30)

        assert result["impact"] == "INFO"
        assert result["avg_qs"] >= 7

    def test_low_qs_returns_high(self, fake_creds):
        """Avg QS < 5 → impact HIGH."""
        from gads_lib.analyze.checks import check_qs_distribution

        rows = [_qs_row("tesla parts", qs=3), _qs_row("tesla bumper", qs=4)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_qs_distribution(fake_creds, days=30)

        assert result["impact"] == "HIGH"
        assert result["avg_qs"] < 5

    def test_medium_qs_returns_medium(self, fake_creds):
        """5 ≤ avg QS < 7 → impact MEDIUM."""
        from gads_lib.analyze.checks import check_qs_distribution

        rows = [_qs_row("tesla parts", qs=5), _qs_row("tesla bumper", qs=6)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_qs_distribution(fake_creds, days=30)

        assert result["impact"] == "MEDIUM"
        assert 5 <= result["avg_qs"] < 7

    def test_deduplication(self, fake_creds):
        """Same keyword text appearing twice (date segments) is counted once for QS avg."""
        from gads_lib.analyze.checks import check_qs_distribution

        rows = [
            _qs_row("tesla parts", qs=7),
            _qs_row("tesla parts", qs=7),   # duplicate text — should be skipped
            _qs_row("tesla bumper", qs=9),
        ]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_qs_distribution(fake_creds, days=30)

        # Only 2 unique keywords: avg = (7 + 9) / 2 = 8.0
        assert result["total_keywords"] == 2
        assert result["avg_qs"] == pytest.approx(8.0, abs=0.1)

    def test_empty_response_no_crash(self, fake_creds):
        """[] → no crash, avg_qs is None."""
        from gads_lib.analyze.checks import check_qs_distribution

        with patch("gads_lib.analyze.checks.run_gaql", return_value=[]):
            result = check_qs_distribution(fake_creds, days=30)

        assert result["avg_qs"] is None
        assert result["total_keywords"] == 0
        assert result["impact"] == "INFO"

    def test_sub_signals_structure(self, fake_creds):
        """Result has sub_signals with post_click, creative, predicted_ctr keys."""
        from gads_lib.analyze.checks import check_qs_distribution

        rows = [_qs_row("tesla parts", qs=7)]
        with patch("gads_lib.analyze.checks.run_gaql", return_value=rows):
            result = check_qs_distribution(fake_creds, days=30)

        assert "sub_signals" in result
        for signal_key in ("post_click", "creative", "predicted_ctr"):
            assert signal_key in result["sub_signals"], f"Missing sub_signal: {signal_key}"
            for band in ("ABOVE_AVERAGE", "AVERAGE", "BELOW_AVERAGE", "UNKNOWN"):
                assert band in result["sub_signals"][signal_key]


# ---------------------------------------------------------------------------
# 8. TestChecksCliCommands
# ---------------------------------------------------------------------------

class TestChecksCliCommands:
    """CLI integration tests — no live API calls, all checks mocked."""

    # ── --help tests (no mocking needed; just verifies command registration) ──

    def test_rsa_lengths_help(self):
        """gads analyze rsa-lengths --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "rsa-lengths", "--help"])
        assert result.exit_code == 0, result.output

    def test_rsa_duplicates_help(self):
        """gads analyze rsa-duplicates --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "rsa-duplicates", "--help"])
        assert result.exit_code == 0, result.output

    def test_dki_help(self):
        """gads analyze dki --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "dki", "--help"])
        assert result.exit_code == 0, result.output

    def test_ad_schedule_help(self):
        """gads analyze ad-schedule --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "ad-schedule", "--help"])
        assert result.exit_code == 0, result.output

    def test_attribution_help(self):
        """gads analyze attribution --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "attribution", "--help"])
        assert result.exit_code == 0, result.output

    def test_budget_is_help(self):
        """gads analyze budget-is --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "budget-is", "--help"])
        assert result.exit_code == 0, result.output

    def test_qs_distribution_help(self):
        """gads analyze qs-distribution --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "qs-distribution", "--help"])
        assert result.exit_code == 0, result.output

    # ── --json shape tests ──

    def test_rsa_lengths_json_shape(self, fake_creds):
        """analyze rsa-lengths --json emits parseable JSON with expected keys."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        mock_result = {
            "window": {"from": "2026-05-01", "to": "2026-05-31", "days": 30},
            "currency": "AED",
            "total_ads": 0,
            "total_headlines": 0,
            "total_descriptions": 0,
            "short_headlines": [],
            "short_descriptions": [],
            "pct_headlines_short": 0.0,
            "pct_descriptions_short": 0.0,
            "impact": "INFO",
        }

        runner = CliRunner()
        with patch("gads_lib.cli.get_credentials", return_value=fake_creds), \
             patch("gads_lib.analyze.checks.check_rsa_lengths", return_value=mock_result):
            result = runner.invoke(cli, ["analyze", "rsa-lengths", "--json"])

        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        for key in ("window", "total_ads", "short_headlines", "impact"):
            assert key in parsed, f"Missing key in JSON output: {key}"

    def test_attribution_json_shape(self, fake_creds):
        """analyze attribution --json emits parseable JSON with expected keys."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        mock_result = {
            "total_conversion_actions": 2,
            "last_click_actions": [],
            "data_driven_actions": ["Purchase", "Lead"],
            "other_actions": [],
            "impact": "INFO",
            "recommendation": "Good — no LAST_CLICK attribution actions found.",
        }

        runner = CliRunner()
        with patch("gads_lib.cli.get_credentials", return_value=fake_creds), \
             patch("gads_lib.analyze.checks.check_attribution_model", return_value=mock_result):
            result = runner.invoke(cli, ["analyze", "attribution", "--json"])

        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        for key in ("total_conversion_actions", "last_click_actions", "impact"):
            assert key in parsed, f"Missing key in JSON output: {key}"

    # ── Top-level audit command tests ──

    def test_audit_top_level_help(self):
        """gads audit --help exits 0 and shows --format and --days options."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["audit", "--help"])
        assert result.exit_code == 0, result.output
        assert "--format" in result.output
        assert "--days" in result.output

    def test_audit_top_level_json(self, fake_creds):
        """gads audit --format json with mocked analyze_audit returns valid JSON."""
        from click.testing import CliRunner
        from gads_lib.cli import cli
        from gads_lib.analyze.audit import _WEIGHTS

        minimal_sections = [
            {
                "id": k,
                "name": k,
                "score": 100,
                "weight": v,
                "weighted_contribution": v,
                "status": "pass",
                "details": {},
            }
            for k, v in _WEIGHTS.items()
        ]
        mock_result = {
            "window": {"from": "2026-05-01", "to": "2026-05-31", "days": 30},
            "overall_score": 100,
            "grade": "A",
            "sections": minimal_sections,
            "sections_by_id": {s["id"]: s for s in minimal_sections},
            "summary": {"pass": 12, "partial": 0, "fail": 0, "critical_fails": []},
        }

        runner = CliRunner()
        with patch("gads_lib.cli.get_credentials", return_value=fake_creds), \
             patch("gads_lib.analyze.audit.analyze_audit", return_value=mock_result):
            result = runner.invoke(cli, ["audit", "--format", "json"])

        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert "overall_score" in parsed
        assert parsed["grade"] == "A"

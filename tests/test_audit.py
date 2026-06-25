"""Offline pytest tests for gads_lib/analyze/audit.py.

ALL Google Ads API calls (run_gaql) are mocked.  No live HTTP.
"""
from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_rsa_row(ad_id="1", campaign="Camp-A", headlines=None, descriptions=None,
                  ad_strength="GOOD", impressions=100):
    """Minimal GAQL row dict mimicking the ad_group_ad resource shape."""
    if headlines is None:
        headlines = [{"text": "Buy Tesla Parts"}, {"text": "Fast UAE Delivery"}]
    if descriptions is None:
        descriptions = [{"text": "Shop OEM + Used Tesla Parts at Talas AE"}]
    return {
        "adGroupAd": {
            "ad": {
                "id": ad_id,
                "responsiveSearchAd": {
                    "headlines": headlines,
                    "descriptions": descriptions,
                },
            },
            "adStrength": ad_strength,
            "status": "ENABLED",
        },
        "campaign": {"name": campaign},
        "adGroup": {"name": "AdGroup-1"},
        "metrics": {"impressions": impressions},
    }


def _make_conv_row(name="WhatsApp Click", model="LAST_CLICK", category="DEFAULT"):
    return {
        "conversionAction": {
            "name": name,
            "status": "ENABLED",
            "countingType": "MANY_PER_CLICK",
            "category": category,
            "attributionModelSettings": {"attributionModel": model},
        }
    }


def _make_camp_row(name="Camp-A", status="ENABLED"):
    return {"campaign": {"name": name, "status": status}, "metrics": {}}


def _make_kw_is_row(camp_name, budget_lost=0.05):
    return {
        "campaign": {"name": camp_name, "status": "ENABLED"},
        "metrics": {"searchBudgetLostImpressionShare": budget_lost},
    }


def _make_kw_qs_row(kw_text, qs=7, post_click="ABOVE_AVERAGE", creative="AVERAGE",
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


def _make_shared_set_row(name="Negatives", count=15):
    return {"sharedSet": {"name": name, "type": "NEGATIVE_KEYWORDS", "memberCount": count}}


def _make_neg_kw_row(camp_name, kw="near me"):
    return {
        "campaign": {"name": camp_name},
        "campaignCriterion": {"keyword": {"text": kw}, "negative": True, "type": "KEYWORD"},
    }


def _make_camp_asset_row(camp_name, asset_type="SITELINK"):
    return {
        "campaign": {"name": camp_name},
        "campaignAsset": {"assetType": asset_type, "status": "ENABLED"},
    }


def _make_schedule_row(camp_name):
    return {
        "campaign": {"name": camp_name, "status": "ENABLED"},
        "campaignCriterion": {
            "type": "AD_SCHEDULE",
            "adSchedule": {"dayOfWeek": "MONDAY", "startHour": 9},
        },
    }


# ---------------------------------------------------------------------------
# Full audit function tests
# ---------------------------------------------------------------------------

class TestAnalyzeAuditStructure:
    """Verify the top-level output shape of analyze_audit."""

    def test_output_has_required_top_level_keys(self, fake_creds):
        """analyze_audit returns dict with window, overall_score, grade, sections, summary."""
        from gads_lib.analyze.audit import analyze_audit

        rsa_rows = [_make_rsa_row(ad_id="1")]
        camp_rows = [_make_camp_row("Camp-A")]
        conv_rows = [_make_conv_row(model="DATA_DRIVEN")]
        is_rows = [_make_kw_is_row("Camp-A", budget_lost=0.05)]
        qs_rows = [_make_kw_qs_row("tesla parts", qs=7)]
        shared_rows = [_make_shared_set_row()]
        asset_rows = [_make_camp_asset_row("Camp-A")]
        schedule_rows = [_make_schedule_row("Camp-A")]

        def _side_effect(creds, query):
            q = query.strip().upper()
            if "FROM AD_GROUP_AD" in q:
                return rsa_rows
            if "FROM CAMPAIGN_CRITERION" in q and "AD_SCHEDULE" in q:
                return schedule_rows
            if "FROM CAMPAIGN_CRITERION" in q and "NEGATIVE" in q:
                return []
            if "FROM CAMPAIGN_CRITERION" in q:
                return schedule_rows
            if "FROM CAMPAIGN\n" in q or "FROM CAMPAIGN " in q:
                if "SEARCH_BUDGET" in q:
                    return is_rows
                return camp_rows
            if "FROM CONVERSION_ACTION" in q:
                return conv_rows
            if "FROM KEYWORD_VIEW" in q:
                return qs_rows
            if "FROM SHARED_SET" in q:
                return shared_rows
            if "FROM CAMPAIGN_ASSET" in q:
                return asset_rows
            return []

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_side_effect):
            result = analyze_audit(fake_creds, days=30)

        assert "window" in result
        assert "overall_score" in result
        assert "grade" in result
        assert "sections" in result
        assert "sections_by_id" in result
        assert "summary" in result

        assert len(result["sections"]) == 12
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
        assert result["grade"] in ("A", "B", "C", "D", "F")

    def test_sections_have_required_keys(self, fake_creds):
        """Each section dict has id, name, score, weight, weighted_contribution, status, details."""
        from gads_lib.analyze.audit import analyze_audit

        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            result = analyze_audit(fake_creds, days=7)

        for s in result["sections"]:
            assert "id" in s, f"Section missing 'id': {s}"
            assert "name" in s, f"Section missing 'name': {s}"
            assert "score" in s, f"Section missing 'score': {s}"
            assert "weight" in s, f"Section missing 'weight': {s}"
            assert "weighted_contribution" in s
            assert "status" in s
            assert "details" in s
            assert s["score"] in (0, 50, 100), f"Score must be 0/50/100, got {s['score']}"
            assert s["status"] in ("pass", "partial", "fail")

    def test_weights_sum_to_100(self):
        """Section weights must sum to 100."""
        from gads_lib.analyze.audit import _WEIGHTS
        assert sum(_WEIGHTS.values()) == 100

    def test_sections_by_id_matches_sections_list(self, fake_creds):
        """sections_by_id is a dict mirror of the sections list keyed by id."""
        from gads_lib.analyze.audit import analyze_audit

        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            result = analyze_audit(fake_creds, days=7)

        for s in result["sections"]:
            assert s["id"] in result["sections_by_id"]
            assert result["sections_by_id"][s["id"]]["score"] == s["score"]


# ---------------------------------------------------------------------------
# Section-level unit tests
# ---------------------------------------------------------------------------

class TestRsaHeadlineLength:
    """Section 1 — headline length ≤ 30 chars."""

    def test_all_within_limit_scores_100(self):
        from gads_lib.analyze.audit import _check_rsa_headline_length
        ads = [{"headlines": ["Short headline", "Also short"], "descriptions": []}]
        score, details = _check_rsa_headline_length(ads)
        assert score == 100
        assert details["over_limit"] == 0

    def test_one_over_limit_out_of_ten_scores_50(self):
        from gads_lib.analyze.audit import _check_rsa_headline_length
        within = [f"H{i}" for i in range(9)]
        over = ["This headline is way too long and exceeds 30 chars limit"]
        ads = [{"headlines": within + over, "descriptions": []}]
        score, details = _check_rsa_headline_length(ads)
        assert score == 50
        assert details["over_limit"] == 1

    def test_majority_over_limit_scores_0(self):
        from gads_lib.analyze.audit import _check_rsa_headline_length
        # 4 over out of 4 = 100% > 25% threshold
        over = ["This headline is definitely too long to be within the 30 char limit"] * 4
        ads = [{"headlines": over, "descriptions": []}]
        score, details = _check_rsa_headline_length(ads)
        assert score == 0

    def test_empty_ads_returns_50(self):
        from gads_lib.analyze.audit import _check_rsa_headline_length
        score, details = _check_rsa_headline_length([])
        assert score == 50


class TestRsaDescriptionLength:
    """Section 2 — description length ≤ 90 chars."""

    def test_all_within_limit_scores_100(self):
        from gads_lib.analyze.audit import _check_rsa_description_length
        ads = [{"headlines": [], "descriptions": ["Short description"]}]
        score, details = _check_rsa_description_length(ads)
        assert score == 100

    def test_over_90_chars_scores_0_when_majority(self):
        from gads_lib.analyze.audit import _check_rsa_description_length
        long_desc = "x" * 95
        ads = [{"headlines": [], "descriptions": [long_desc, long_desc, long_desc, long_desc]}]
        score, _ = _check_rsa_description_length(ads)
        assert score == 0


class TestRsaHeadlineDiversity:
    """Section 3 — intra-RSA duplicate headline detection."""

    def test_no_duplicates_scores_100(self):
        from gads_lib.analyze.audit import _check_rsa_headline_diversity
        ads = [{
            "ad_id": "1",
            "campaign": "Camp",
            "headlines": ["Headline A", "Headline B", "Headline C"],
            "descriptions": [],
        }]
        score, details = _check_rsa_headline_diversity(ads)
        assert score == 100
        assert details["ads_with_dupes"] == 0

    def test_duplicate_detected(self):
        from gads_lib.analyze.audit import _check_rsa_headline_diversity
        ads = [{
            "ad_id": "2",
            "campaign": "Camp",
            "headlines": ["Tesla Parts", "Tesla Parts", "Unique"],  # duplicate
            "descriptions": [],
        }]
        score, details = _check_rsa_headline_diversity(ads)
        assert details["ads_with_dupes"] == 1
        # 1/1 ads with dupes = 100% > 25% → score 0
        assert score == 0

    def test_case_insensitive_duplicate(self):
        from gads_lib.analyze.audit import _check_rsa_headline_diversity
        ads = [{
            "ad_id": "3",
            "campaign": "Camp",
            "headlines": ["Tesla Parts UAE", "tesla parts uae"],  # same, different case
            "descriptions": [],
        }]
        score, details = _check_rsa_headline_diversity(ads)
        assert details["ads_with_dupes"] == 1


class TestRsaAdStrength:
    """Section 4 — ad strength EXCELLENT/GOOD."""

    def test_all_excellent_scores_100(self):
        from gads_lib.analyze.audit import _check_rsa_ad_strength
        ads = [{"ad_strength": "EXCELLENT"}, {"ad_strength": "EXCELLENT"}]
        score, details = _check_rsa_ad_strength(ads)
        assert score == 100

    def test_good_scores_100(self):
        from gads_lib.analyze.audit import _check_rsa_ad_strength
        ads = [{"ad_strength": "GOOD"}]
        score, _ = _check_rsa_ad_strength(ads)
        assert score == 100

    def test_average_scores_50(self):
        from gads_lib.analyze.audit import _check_rsa_ad_strength
        ads = [{"ad_strength": "AVERAGE"}]
        score, _ = _check_rsa_ad_strength(ads)
        assert score == 50

    def test_poor_scores_0(self):
        from gads_lib.analyze.audit import _check_rsa_ad_strength
        ads = [{"ad_strength": "POOR"}]
        score, _ = _check_rsa_ad_strength(ads)
        assert score == 0


class TestDkiPresence:
    """Section 5 — DKI {keyword:...} detected."""

    def test_dki_present_scores_100(self):
        from gads_lib.analyze.audit import _check_dki_presence
        ads = [{
            "ad_id": "1",
            "headlines": ["{keyword:Tesla Parts} UAE", "Fast Delivery"],
            "descriptions": ["Buy Tesla Parts"],
        }]
        score, details = _check_dki_presence(ads)
        assert score == 100
        assert details["dki_ad_count"] == 1

    def test_no_dki_scores_0(self):
        from gads_lib.analyze.audit import _check_dki_presence
        ads = [{
            "ad_id": "1",
            "headlines": ["Tesla Parts UAE", "Fast Delivery"],
            "descriptions": ["Buy Tesla Parts"],
        }]
        score, details = _check_dki_presence(ads)
        assert score == 0
        assert details["dki_ad_count"] == 0

    def test_empty_ads_scores_0(self):
        from gads_lib.analyze.audit import _check_dki_presence
        score, _ = _check_dki_presence([])
        assert score == 0


class TestAttributionModel:
    """Section 7 — conversion attribution model check."""

    def test_all_data_driven_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_attribution_model
        rows = [_make_conv_row("Conv1", model="DATA_DRIVEN")]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_attribution_model(fake_creds)
        assert score == 100
        assert details["last_click_count"] == 0

    def test_all_last_click_scores_0(self, fake_creds):
        from gads_lib.analyze.audit import _check_attribution_model
        rows = [
            _make_conv_row("Conv1", model="LAST_CLICK"),
            _make_conv_row("Conv2", model="LAST_CLICK"),
        ]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_attribution_model(fake_creds)
        assert score == 0
        assert details["last_click_count"] == 2

    def test_mixed_scores_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_attribution_model
        rows = [
            _make_conv_row("Conv1", model="LAST_CLICK"),
            _make_conv_row("Conv2", model="DATA_DRIVEN"),
        ]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_attribution_model(fake_creds)
        assert score == 50

    def test_no_conversions_returns_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_attribution_model
        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            score, details = _check_attribution_model(fake_creds)
        assert score == 50
        assert "note" in details


class TestBudgetLostIS:
    """Section 8 — search_budget_lost_impression_share < 20%."""

    def test_low_budget_lost_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_budget_lost_is
        rows = [_make_kw_is_row("Camp-A", budget_lost=0.05)]  # 5% < 10%
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_budget_lost_is(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 100
        assert details["avg_budget_lost_is_pct"] == pytest.approx(5.0, abs=0.1)

    def test_mid_budget_lost_scores_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_budget_lost_is
        rows = [_make_kw_is_row("Camp-A", budget_lost=0.15)]  # 15% → between 10-20%
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_budget_lost_is(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 50

    def test_high_budget_lost_scores_0(self, fake_creds):
        from gads_lib.analyze.audit import _check_budget_lost_is
        rows = [_make_kw_is_row("Camp-A", budget_lost=0.30)]  # 30% ≥ 20%
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_budget_lost_is(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 0

    def test_sentinel_value_excluded(self, fake_creds):
        """Sentinel values (>1.5) from the API are excluded gracefully."""
        from gads_lib.analyze.audit import _check_budget_lost_is
        rows = [{
            "campaign": {"name": "Camp-A", "status": "ENABLED"},
            "metrics": {"searchBudgetLostImpressionShare": 9.22337203685478e+18},  # sentinel
        }]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_budget_lost_is(fake_creds, "2026-05-01", "2026-05-31")
        # Sentinel excluded → no valid data → should return 50 with note
        assert score == 50


class TestKeywordQS:
    """Section 9 — keyword Quality Score distribution."""

    def test_high_qs_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_keyword_qs
        rows = [
            _make_kw_qs_row("tesla parts", qs=8),
            _make_kw_qs_row("tesla bumper", qs=7),
        ]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_keyword_qs(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 100
        assert details["avg_qs"] == pytest.approx(7.5, abs=0.1)

    def test_medium_qs_scores_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_keyword_qs
        rows = [_make_kw_qs_row("tesla parts", qs=5)]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_keyword_qs(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 50

    def test_low_qs_scores_0(self, fake_creds):
        from gads_lib.analyze.audit import _check_keyword_qs
        rows = [_make_kw_qs_row("tesla parts", qs=3)]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_keyword_qs(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 0

    def test_no_qs_data_returns_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_keyword_qs
        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            score, details = _check_keyword_qs(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 50
        assert details["avg_qs"] is None

    def test_deduplicates_keywords(self, fake_creds):
        """Duplicate keyword text rows (date segments) are deduplicated for QS avg."""
        from gads_lib.analyze.audit import _check_keyword_qs
        # Same keyword twice (simulating date-segment rows)
        rows = [
            _make_kw_qs_row("tesla parts", qs=7),
            _make_kw_qs_row("tesla parts", qs=7),  # duplicate
            _make_kw_qs_row("tesla bumper", qs=9),
        ]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_keyword_qs(fake_creds, "2026-05-01", "2026-05-31")
        assert details["qs_values_count"] == 2  # deduplicated


class TestNegativeCoverage:
    """Section 10 — negative keyword coverage."""

    def test_shared_list_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_negative_coverage
        shared_rows = [_make_shared_set_row()]

        def _se(creds, query):
            q = query.upper()
            if "SHARED_SET" in q:
                return shared_rows
            return []

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_se):
            score, details = _check_negative_coverage(fake_creds)
        assert score == 100
        assert details["shared_negative_lists"] == 1

    def test_campaign_negatives_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_negative_coverage
        neg_rows = [_make_neg_kw_row("Camp-A")]

        def _se(creds, query):
            q = query.upper()
            if "SHARED_SET" in q:
                return []
            if "CAMPAIGN_CRITERION" in q:
                return neg_rows
            return []

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_se):
            score, details = _check_negative_coverage(fake_creds)
        assert score == 100

    def test_no_negatives_scores_0(self, fake_creds):
        from gads_lib.analyze.audit import _check_negative_coverage
        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            score, details = _check_negative_coverage(fake_creds)
        assert score == 0


class TestConversionPrimary:
    """Section 11 — primary conversion action present."""

    def test_primary_category_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_conversion_primary
        rows = [_make_conv_row(category="PURCHASE")]
        with patch("gads_lib.analyze.audit.run_gaql", return_value=rows):
            score, details = _check_conversion_primary(fake_creds)
        assert score == 100

    def test_no_conversions_returns_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_conversion_primary
        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            score, details = _check_conversion_primary(fake_creds)
        assert score == 50


class TestSitelinkCoverage:
    """Section 12 — sitelink asset coverage."""

    def test_all_campaigns_covered_scores_100(self, fake_creds):
        from gads_lib.analyze.audit import _check_sitelink_coverage
        camp_rows = [_make_camp_row("Camp-A")]
        asset_rows = [_make_camp_asset_row("Camp-A")]

        def _se(creds, query):
            q = query.upper()
            if "CAMPAIGN_ASSET" in q:
                return asset_rows
            return camp_rows

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_se):
            score, details = _check_sitelink_coverage(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 100
        assert details["covered"] == 1
        assert details["missing_sitelinks"] == []

    def test_partial_coverage_scores_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_sitelink_coverage
        camp_rows = [_make_camp_row("Camp-A"), _make_camp_row("Camp-B")]
        asset_rows = [_make_camp_asset_row("Camp-A")]  # only Camp-A has sitelinks

        def _se(creds, query):
            q = query.upper()
            if "CAMPAIGN_ASSET" in q:
                return asset_rows
            return camp_rows

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_se):
            score, details = _check_sitelink_coverage(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 50
        assert "Camp-B" in details["missing_sitelinks"]

    def test_no_sitelinks_scores_0(self, fake_creds):
        from gads_lib.analyze.audit import _check_sitelink_coverage
        camp_rows = [_make_camp_row("Camp-A")]

        def _se(creds, query):
            q = query.upper()
            if "CAMPAIGN_ASSET" in q:
                return []
            return camp_rows

        with patch("gads_lib.analyze.audit.run_gaql", side_effect=_se):
            score, details = _check_sitelink_coverage(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 0

    def test_no_active_campaigns_returns_50(self, fake_creds):
        from gads_lib.analyze.audit import _check_sitelink_coverage
        with patch("gads_lib.analyze.audit.run_gaql", return_value=[]):
            score, details = _check_sitelink_coverage(fake_creds, "2026-05-01", "2026-05-31")
        assert score == 50


# ---------------------------------------------------------------------------
# Render tests
# ---------------------------------------------------------------------------

class TestRenderAudit:
    """Verify render_audit does not crash and respects as_json flag."""

    def _minimal_result(self):
        """Minimal result dict for render testing."""
        from gads_lib.analyze.audit import _WEIGHTS, _check_rsa_headline_length
        sections = []
        for sec_id, w in _WEIGHTS.items():
            sections.append({
                "id": sec_id,
                "name": sec_id.replace("_", " ").title(),
                "score": 100,
                "weight": w,
                "weighted_contribution": w,
                "status": "pass",
                "details": {},
            })
        return {
            "window": {"from": "2026-05-01", "to": "2026-05-31", "days": 30},
            "overall_score": 100,
            "grade": "A",
            "sections": sections,
            "sections_by_id": {s["id"]: s for s in sections},
            "summary": {"pass": 12, "partial": 0, "fail": 0, "critical_fails": []},
        }

    def test_render_table_does_not_raise(self, capsys):
        from gads_lib.analyze.audit import render_audit
        render_audit(self._minimal_result(), as_json=False)
        out = capsys.readouterr().out
        assert "Structural Compliance Audit" in out
        assert "100" in out

    def test_render_json_emits_valid_json(self, capsys):
        from gads_lib.analyze.audit import render_audit
        render_audit(self._minimal_result(), as_json=True)
        out = capsys.readouterr().out
        parsed = json.loads(out)
        assert "overall_score" in parsed
        assert parsed["grade"] == "A"

    def test_render_shows_fail_sections(self, capsys):
        from gads_lib.analyze.audit import render_audit
        result = self._minimal_result()
        # Force one failure
        result["sections"][0]["score"] = 0
        result["sections"][0]["status"] = "fail"
        result["summary"]["fail"] = 1
        result["summary"]["pass"] = 11
        render_audit(result, as_json=False)
        out = capsys.readouterr().out
        assert "FAIL" in out


# ---------------------------------------------------------------------------
# CLI integration test
# ---------------------------------------------------------------------------

class TestAuditCliCommand:
    """Verify the gads analyze audit CLI command is registered and callable."""

    def test_analyze_audit_help(self):
        """gads analyze audit --help exits 0."""
        from click.testing import CliRunner
        from gads_lib.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["analyze", "audit", "--help"])
        assert result.exit_code == 0, result.output
        assert "audit" in result.output.lower()
        assert "--days" in result.output
        assert "--json" in result.output

    def test_analyze_audit_json_output(self, fake_creds):
        """gads analyze audit --json invokes analyze_audit and emits JSON."""
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
            result = runner.invoke(cli, ["analyze", "audit", "--json", "--days", "7"])

        assert result.exit_code == 0, result.output
        parsed = json.loads(result.output)
        assert parsed["overall_score"] == 100
        assert parsed["grade"] == "A"
        assert len(parsed["sections"]) == 12

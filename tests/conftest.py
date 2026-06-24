"""Shared fixtures for the gads-cli offline test suite."""
import os
import pytest
from unittest.mock import MagicMock


# ── Environment stubs — must be set BEFORE gads_lib imports resolve config ──
# These are set at module load time so config.py picks them up on first import.
os.environ.setdefault("GOOGLE_ADS_DEVELOPER_TOKEN", "fake-dev-token")
os.environ.setdefault("GOOGLE_ADS_CUSTOMER_ID", "1234567890")
os.environ.setdefault("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "9999999999")
os.environ.setdefault("GOOGLE_MERCHANT_CENTER_ID", "88887777")
os.environ.setdefault("GOOGLE_GA4_PROPERTY_ID", "271773771")
os.environ.setdefault("GADS_PROJECT_ROOT", "/tmp/gads-test-scope")


@pytest.fixture
def fake_creds():
    """A minimal mock OAuth credentials object with a valid-looking token."""
    creds = MagicMock()
    creds.token = "ya29.fake-access-token"
    return creds

import json

import click
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from .config import CREDS_PATH
from .output import EXIT_CODES


def get_credentials():
    """Load and refresh OAuth credentials."""
    if not CREDS_PATH.exists():
        click.secho(f"✗ Credentials not found: {CREDS_PATH}", fg="red", err=True)
        raise SystemExit(1)

    with open(CREDS_PATH) as f:
        creds_data = json.load(f)

    creds = Credentials.from_authorized_user_info(creds_data)
    if creds.expired:
        try:
            creds.refresh(Request())
        except RefreshError as e:
            click.secho(f"✗ OAuth token refresh failed: {e}", fg="red", err=True)
            click.secho(
                "  The refresh token is likely expired or has been revoked. "
                "Fix: python generate_token.py (or gads-cli/generate_token.py) "
                "to re-authenticate.",
                fg="yellow",
                err=True,
            )
            raise SystemExit(EXIT_CODES["AUTH"])
        with open(CREDS_PATH, "w") as f:
            f.write(creds.to_json())
    return creds

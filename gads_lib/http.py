import json
import sys

import click
import requests

from .config import DEV_TOKEN, LOGIN_CUSTOMER_ID
from .output import EXIT_CODES, classify_api_error, offer_gcloud_enable


def request_json(method, url, *, headers=None, params=None, json_body=None, timeout=30, as_json=False):
    resp = requests.request(
        method,
        url,
        headers=headers,
        params=params,
        json=json_body,
        timeout=timeout,
    )
    if resp.status_code >= 400:
        classified = classify_api_error(resp.status_code, resp.text, url=url)
        if classified:
            if as_json:
                sys.stdout.write(json.dumps({"error": classified}) + "\n")
                sys.stdout.flush()
                raise SystemExit(EXIT_CODES["API"])
            code = classified["code"]  # noqa: F841
            msg = classified["message"]
            action = classified.get("action")
            if action == "run_gcloud":
                service = classified.get("service", "unknown")
                project_id = classified.get("project_id")
                click.secho(f"✗ {msg}", fg="red", err=True)
                click.secho(f"  API not enabled: {service}.googleapis.com", fg="yellow", err=True)
                offer_gcloud_enable(service, project_id=project_id, yes=False)
            elif action == "regen_token":
                scope = classified.get("scope", "")
                click.secho("✗ Insufficient OAuth scope.", fg="red", err=True)
                click.secho(f"  Missing scope: {scope}", fg="yellow", err=True)
                click.secho(
                    "  Fix: python generate_token.py  (re-consent to add the scope)",
                    fg="cyan",
                    err=True,
                )
            elif action == "register_merchant":
                click.secho(f"✗ {msg}", fg="red", err=True)
                click.secho(
                    "  Merchant Center not registered as API developer.", fg="yellow", err=True
                )
                click.secho(
                    f"  Register at: {classified.get('url', '')}", fg="cyan", err=True
                )
            elif action == "request_allowlist":
                click.secho(f"✗ {msg}", fg="red", err=True)
                click.secho(
                    f"  Request access/allowlist at: {classified.get('url', '')}",
                    fg="cyan",
                    err=True,
                )
            raise SystemExit(EXIT_CODES["API"])
        else:
            detail = resp.text[:1200]
            if as_json:
                sys.stdout.write(json.dumps({
                    "error": {
                        "code": "API_ERROR",
                        "message": detail,
                        "action": None,
                        "service": None,
                        "scope": None,
                        "url": None,
                        "project_id": None,
                    }
                }) + "\n")
                sys.stdout.flush()
                raise SystemExit(EXIT_CODES["API"])
            click.secho(f"✗ API Error {resp.status_code}: {detail}", fg="red", err=True)
            raise SystemExit(EXIT_CODES["API"])
    if not resp.text:
        return {}
    return resp.json()


def get_bearer_headers(creds):
    return {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json",
    }


def get_ads_headers(creds):
    return {
        **get_bearer_headers(creds),
        "developer-token": DEV_TOKEN,
        "login-customer-id": LOGIN_CUSTOMER_ID,
    }

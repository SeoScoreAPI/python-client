"""
SEO Score API - Python Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Audit any URL for SEO issues with one function call.

Usage:
    from seoscoreapi import audit, signup

    # Get a free API key
    key = signup("you@example.com")

    # Run an audit
    result = audit("https://example.com", api_key=key)
    print(f"Score: {result['score']}/100 ({result['grade']})")

Full docs: https://seoscoreapi.com/docs
"""

import requests

BASE_URL = "https://seoscoreapi.com"
__version__ = "1.0.0"


def signup(email: str) -> str:
    """Sign up for a free API key. Returns the raw key (save it — shown only once)."""
    r = requests.post(f"{BASE_URL}/signup", json={"email": email})
    r.raise_for_status()
    return r.json()["api_key"]


def audit(url: str, api_key: str) -> dict:
    """Run an SEO audit on a URL. Returns score, grade, checks, and priorities."""
    r = requests.get(f"{BASE_URL}/audit", params={"url": url}, headers={"X-API-Key": api_key})
    r.raise_for_status()
    return r.json()


def batch_audit(urls: list[str], api_key: str) -> dict:
    """Audit multiple URLs (paid plans only). Returns list of results."""
    r = requests.post(f"{BASE_URL}/audit/batch", json={"urls": urls}, headers={"X-API-Key": api_key})
    r.raise_for_status()
    return r.json()


def usage(api_key: str) -> dict:
    """Check your API usage and limits."""
    r = requests.get(f"{BASE_URL}/usage", headers={"X-API-Key": api_key})
    r.raise_for_status()
    return r.json()


def add_monitor(url: str, api_key: str, frequency: str = "daily") -> dict:
    """Set up score monitoring for a URL (paid plans only)."""
    r = requests.post(f"{BASE_URL}/monitors", json={"url": url, "frequency": frequency}, headers={"X-API-Key": api_key})
    r.raise_for_status()
    return r.json()


def list_monitors(api_key: str) -> list:
    """List your active monitors."""
    r = requests.get(f"{BASE_URL}/monitors", headers={"X-API-Key": api_key})
    r.raise_for_status()
    return r.json()["monitors"]


def report_url(domain: str) -> str:
    """Get the shareable report URL for a domain."""
    return f"{BASE_URL}/report/{domain}"

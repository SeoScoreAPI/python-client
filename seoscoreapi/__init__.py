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

from __future__ import annotations  # lazy annotations so `list[str]` works on Python 3.8

import os
import time
from typing import Callable, Optional

import requests

BASE_URL = "https://seoscoreapi.com"
# Deep Site Audit is served on the main host (POST /site-audit,
# GET /site-audit/{job_id}, GET /deep-audit/usage). Override per call with
# ``base_url=``, globally by assigning ``seoscoreapi.DEEP_AUDIT_URL``, or with the
# ``SEOSCORE_DEEP_AUDIT_URL`` environment variable.
DEEP_AUDIT_URL = os.environ.get("SEOSCORE_DEEP_AUDIT_URL") or BASE_URL
# Legacy dedicated engine host. Still serves the same endpoints (its quota
# endpoint is plain ``/usage``); pass it as ``base_url`` if you need it.
ENGINE_URL = "https://engine.seoscoreapi.com"
__version__ = "1.5.0"

_HEADERS = {"User-Agent": f"seoscoreapi-python/{__version__}"}
_TIMEOUT = 30  # seconds — default per-request timeout for engine calls


def signup(email: str) -> str:
    """Sign up for a free API key. Returns the raw key (save it — shown only once)."""
    r = requests.post(f"{BASE_URL}/signup", json={"email": email}, headers=_HEADERS)
    r.raise_for_status()
    return r.json()["api_key"]


def audit(url: str, api_key: str) -> dict:
    """Run an SEO audit on a URL. Returns score, grade, checks, and priorities."""
    r = requests.get(f"{BASE_URL}/audit", params={"url": url}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def batch_audit(urls: list[str], api_key: str) -> dict:
    """Audit multiple URLs (paid plans only). Returns list of results."""
    r = requests.post(f"{BASE_URL}/audit/batch", json={"urls": urls}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def usage(api_key: str) -> dict:
    """Check your API usage and limits."""
    r = requests.get(f"{BASE_URL}/usage", headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def add_monitor(
    url: str,
    api_key: str,
    frequency: str = "daily",
    webhook_url: Optional[str] = None,
    alert_threshold: int = 5,
) -> dict:
    """Set up score monitoring for a URL (paid plans only).

    `webhook_url` (optional): receives a POST whenever the score drops
    by `alert_threshold` points or more. Slack incoming-webhook URLs are
    auto-formatted as Block Kit messages; any other https endpoint
    receives the raw event JSON.
    """
    payload: dict = {"url": url, "frequency": frequency, "alert_threshold": alert_threshold}
    if webhook_url:
        payload["webhook_url"] = webhook_url
    r = requests.post(f"{BASE_URL}/monitors", json=payload, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def list_monitors(api_key: str) -> list:
    """List your active monitors."""
    r = requests.get(f"{BASE_URL}/monitors", headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()["monitors"]


def scoreboard_opt_out(api_key: str, opt_out: bool = True) -> dict:
    """Opt in or out of the public SEO scoreboard."""
    r = requests.put(f"{BASE_URL}/scoreboard/opt-out", params={"opt_out": str(opt_out).lower()}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def compare(urls: list[str], api_key: str) -> dict:
    """Compare 2–5 URLs side by side with a structured diff (Basic plan or higher).

    Returns each URL's score and category breakdown plus a `diff`
    object describing who is ahead and by how much, per category and
    per URL pair.
    """
    r = requests.post(f"{BASE_URL}/compare", json={"urls": urls}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def competitive_audit(url: str, competitor_url: str, keyword: str, api_key: str) -> dict:
    """Run a head-to-head competitive audit (Pro plan or higher). Returns gap score, per-check diffs, and action items."""
    r = requests.post(f"{BASE_URL}/audit/competitive", json={"url": url, "competitor_url": competitor_url, "keyword": keyword}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def report_url(domain: str) -> str:
    """Get the shareable report URL for a domain."""
    return f"{BASE_URL}/report/{domain}"


def history(url: str, api_key: str, limit: int = 100, since: Optional[float] = None) -> dict:
    """Get historical audit scores and trend summary for a URL (Starter plan or higher)."""
    params: dict = {"url": url, "limit": limit}
    if since is not None:
        params["since"] = since
    r = requests.get(f"{BASE_URL}/history", params=params, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def history_domains(api_key: str) -> list:
    """List every domain audited by this key with latest score and 30-day trend (Starter plan or higher)."""
    r = requests.get(f"{BASE_URL}/history/domains", headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()["domains"]


# --- Deep Site Audit (Pro/Ultra, or credits) ---------------------------------

def _deep_base(base_url: Optional[str]) -> str:
    return (base_url or DEEP_AUDIT_URL).rstrip("/")


def _usage_path(base: str) -> str:
    # The main host serves the engine's quota at /deep-audit/usage (its own
    # /usage is the per-URL audit allowance); the legacy engine host uses /usage.
    return "/usage" if base.split("://", 1)[-1].startswith("engine.") else "/deep-audit/usage"


def _start(url: str, api_key: str, base: str, options: dict) -> requests.Response:
    return requests.post(
        f"{base}/site-audit",
        json={"url": url, **options},
        headers={"X-API-Key": api_key, **_HEADERS},
        timeout=_TIMEOUT,
    )


def site_audit(url: str, api_key: str, *, base_url: Optional[str] = None, **options) -> dict:
    """Start a Deep Site Audit. Asynchronous: returns a job
    ``{"job_id", "status", "poll"}``; poll it with :func:`get_site_audit` or
    block on it with :func:`wait_for_site_audit`.

    Optional keyword args are sent to the API as-is: ``business_type``
    (saas | local_service | ecommerce | storefront | blog | publisher),
    ``is_local``, ``webhook_url``.
    """
    r = _start(url, api_key, _deep_base(base_url), options)
    r.raise_for_status()
    return r.json()


def get_site_audit(job_id: str, api_key: str, *, base_url: Optional[str] = None) -> dict:
    """Poll a Deep Site Audit job. Returns ``status`` plus ``queue_position``/
    ``eta_seconds`` while queued, ``progress``/``stage`` while running, and
    ``result`` when completed (or ``error`` when failed)."""
    r = requests.get(
        f"{_deep_base(base_url)}/site-audit/{job_id}",
        headers={"X-API-Key": api_key, **_HEADERS},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def wait_for_site_audit(
    job_id: str,
    api_key: str,
    *,
    poll_interval: float = 5.0,
    timeout: float = 600.0,
    on_progress: Optional[Callable[[dict], None]] = None,
    base_url: Optional[str] = None,
) -> dict:
    """Poll an existing Deep Site Audit job until it finishes; return its result.

    Honors the server's ETA while queued. Raises ``TimeoutError`` if it isn't
    done within ``timeout`` seconds, or ``RuntimeError`` if the audit fails.
    """
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("Timed out waiting for audit to complete")
        status = get_site_audit(job_id, api_key, base_url=base_url)
        if on_progress:
            on_progress(status)
        state = status.get("status")
        if state == "completed":
            return status["result"]
        if state == "failed":
            raise RuntimeError(status.get("error", "Audit failed"))
        if state == "queued" and status.get("eta_seconds"):
            time.sleep(min(float(status["eta_seconds"]), 15.0))
        else:
            time.sleep(poll_interval)


def deep_audit(
    url: str,
    api_key: str,
    *,
    poll_interval: float = 5.0,
    timeout: float = 600.0,
    on_progress: Optional[Callable[[dict], None]] = None,
    base_url: Optional[str] = None,
    **options,
) -> dict:
    """Start a Deep Site Audit and block until it finishes; return the result dict.

    Retries the submit on queue backpressure (429 + ``Retry-After``), then
    polls with :func:`wait_for_site_audit`. Raises ``TimeoutError`` if it
    doesn't finish within ``timeout`` seconds, or ``RuntimeError`` if it fails.
    """
    base = _deep_base(base_url)
    deadline = time.monotonic() + timeout
    while True:  # submit, retrying on backpressure
        r = _start(url, api_key, base, options)
        if r.status_code == 429:
            retry = float(r.headers.get("Retry-After", 5))
            if time.monotonic() + retry > deadline:
                raise TimeoutError("Timed out waiting for queue capacity")
            time.sleep(retry)
            continue
        r.raise_for_status()
        job = r.json()
        break
    return wait_for_site_audit(
        job["job_id"],
        api_key,
        poll_interval=poll_interval,
        timeout=max(deadline - time.monotonic(), 0.0),
        on_progress=on_progress,
        base_url=base,
    )


def deep_audit_usage(api_key: str, *, base_url: Optional[str] = None) -> dict:
    """Deep Site Audits used/remaining this month for this key
    (``{"tier", "site_audit": {"used", "remaining"}, ...}``)."""
    base = _deep_base(base_url)
    r = requests.get(
        f"{base}{_usage_path(base)}",
        headers={"X-API-Key": api_key, **_HEADERS},
        timeout=_TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def engine_usage(api_key: str, *, base_url: Optional[str] = None) -> dict:
    """Deprecated alias of :func:`deep_audit_usage` (kept for 1.4 callers)."""
    return deep_audit_usage(api_key, base_url=base_url)

"""
SEO Score API - Python Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Audit any URL for SEO issues with one function call.

Usage:
    from seoscoreapi import audit, signup, verify

    # Get a free API key: signup() emails a 6-digit code, verify() returns the key
    signup("you@example.com")
    key = verify("you@example.com", input("Code from the email: "))

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
__version__ = "1.7.1"

_HEADERS = {"User-Agent": f"seoscoreapi-python/{__version__}"}
_TIMEOUT = 30  # seconds — default per-request timeout for engine calls


def signup(email: str) -> dict:
    """Start signup for a free API key. The API emails a 6-digit code to `email`.

    Returns the API's response, normally
    ``{"status": "verification_required", "message": "..."}``. No key is issued
    yet: pass the code to :func:`verify` to get it. The code expires after 10
    minutes. Raises ``requests.HTTPError`` on a rejected address (400) or an
    email that already has an active key (409).
    """
    r = requests.post(f"{BASE_URL}/signup", json={"email": email}, headers=_HEADERS)
    r.raise_for_status()
    return r.json()


def verify(email: str, code: str) -> str:
    """Finish signup: exchange the emailed 6-digit code for the API key.

    Returns the raw key (save it, it is shown only once). Raises
    ``requests.HTTPError`` (400) on a wrong or expired code, or when there is no
    pending signup for `email`; the reason is in ``e.response.json()["detail"]``.
    Five wrong codes void the signup, so call :func:`signup` again after that.
    """
    r = requests.post(
        f"{BASE_URL}/verify",
        json={"email": email, "code": str(code).strip()},
        headers=_HEADERS,
    )
    r.raise_for_status()
    return r.json()["api_key"]


def audit(url: str, api_key: str, cwv: bool = False) -> dict:
    """Run an SEO audit on a URL. Returns score, grade, checks, and priorities.

    ``cwv=True`` adds measured Core Web Vitals (LCP, INP, CLS, FCP, TTFB from Google
    PageSpeed Insights) under ``core_web_vitals``. It is off by default because the
    first measurement of a URL adds about 10 seconds (it is then cached for 24
    hours). Without it ``core_web_vitals["status"]`` is ``"not_requested"``; with
    it, ``"ok"``, or ``"unavailable"`` with a ``reason`` (and ``pending: True`` when
    the measurement is still running: audit the URL again to pick it up).
    """
    params = {"url": url}
    if cwv:
        params["cwv"] = "true"
    r = requests.get(f"{BASE_URL}/audit", params=params, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


def batch_audit(urls: list[str], api_key: str, cwv: bool = False) -> dict:
    """Audit multiple URLs (paid plans only). Returns list of results.

    ``cwv=True`` adds measured Core Web Vitals to every result (see ``audit``). The
    batch then takes longer: allow up to three minutes.
    """
    body: dict = {"urls": urls}
    if cwv:
        body["cwv"] = True
    r = requests.post(f"{BASE_URL}/audit/batch", json=body, headers={"X-API-Key": api_key, **_HEADERS})
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


def remove_monitor(url: str, api_key: str) -> dict:
    """Remove a score monitor (``DELETE /monitors``)."""
    r = requests.delete(f"{BASE_URL}/monitors", json={"url": url}, headers={"X-API-Key": api_key, **_HEADERS})
    r.raise_for_status()
    return r.json()


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


# --- Shared request helpers ---------------------------------------------------

def _auth(api_key: Optional[str]) -> dict:
    return {"X-API-Key": api_key, **_HEADERS} if api_key else dict(_HEADERS)


def _params(**values) -> dict:
    """Query parameters with the unset (None) ones dropped."""
    return {k: v for k, v in values.items() if v is not None}


def _csv(value):
    """Lists become the comma-separated string the API takes; strings pass through."""
    if value is None or isinstance(value, str):
        return value
    return ",".join(str(v) for v in value)


def _get(path: str, api_key: Optional[str], params: Optional[dict] = None) -> requests.Response:
    r = requests.get(f"{BASE_URL}{path}", params=params or None, headers=_auth(api_key))
    r.raise_for_status()
    return r


def _send(method: str, path: str, api_key: str, body: Optional[dict] = None) -> dict:
    r = getattr(requests, method)(f"{BASE_URL}{path}", json=body, headers=_auth(api_key))
    r.raise_for_status()
    return r.json()


# --- Accessibility, exports and single-page analyses -----------------------------

def accessibility_audit(url: str, api_key: str, include: Optional[str] = None) -> dict:
    """Run an ADA / WCAG 2.1 AA accessibility audit (paid plans only).

    Returns the compliance score and grade, lawsuit risk, ``violations`` (WCAG
    2.1 AA failures), ``best_practices``, ``needs_review`` and ``priorities``.
    ADA audits have their own monthly allowance (``ada_monthly``), separate from
    the audit quota; ``usage()`` reports ``ada_remaining``. Pass
    ``include="trackers"`` to add the tracker and pixel inventory to the report.
    A 429 carries ``Retry-After`` and is not counted.
    """
    return _get("/audit/accessibility", api_key, _params(url=url, include=include)).json()


def audit_export(
    url: str,
    api_key: str,
    format: str = "pdf",
    *,
    brand_name: Optional[str] = None,
    brand_color: Optional[str] = None,
    logo_url: Optional[str] = None,
) -> bytes:
    """Run an audit and download it as a report file. Returns the file's bytes.

    ``format`` is ``"pdf"``, ``"md"`` or ``"csv"``. Same audit, usage and plan
    gating as :func:`audit` (it counts as one audit). White-label (Pro and
    Ultra): ``brand_name``, ``brand_color`` (``#rrggbb``) and ``logo_url`` (https
    PNG/JPEG/WebP, max 300 KB) put your agency's name, colour and logo on the
    report; on other plans those parameters return 403.

        open("report.pdf", "wb").write(audit_export("https://example.com", key))
    """
    params = _params(url=url, format=format, brand_name=brand_name, brand_color=brand_color, logo_url=logo_url)
    return _get("/audit/export", api_key, params).content


def ai_readability(url: str, api_key: str) -> dict:
    """Score how well a page can be consumed by AI/LLM systems. Counts as one audit."""
    return _get("/ai-readability", api_key, {"url": url}).json()


def trackers(url: str, api_key: str) -> dict:
    """List the third-party trackers and pixels a page loads.

    Loads the page in a real browser and reports analytics, advertising,
    session-replay, chat and other tools, including pixels a tag manager injects.
    Counts as one audit; a page that can't be loaded returns 422 and is not counted.
    """
    return _get("/trackers", api_key, {"url": url}).json()


def conversion(url: str, api_key: str, page_type: Optional[str] = None) -> dict:
    """Score how well a page turns a visitor into a lead or a sale.

    Scores ``headline``, ``cta``, ``trust``, ``forms`` and ``objections`` from
    0 to 100 and returns ``score``, ``grade``, ``categories``, ``signals`` and
    ``priorities``. ``page_type`` is ``local_service``, ``ecommerce``, ``saas`` or
    ``general`` (detected from the page when omitted). Counts as one audit. Free
    keys get the scores and the first two priorities; paid plans the full list.
    """
    return _get("/conversion", api_key, _params(url=url, page_type=page_type)).json()


def quick_wins(api_key: str, rows: Optional[list] = None, csv: Optional[str] = None, **options) -> dict:
    """Find the page-2 quick wins in your own Search Console data.

    Send ``rows`` (``[{"query", "page", "clicks", "impressions", "position"}]``,
    or the Search Analytics API's own ``{"keys": [...], ...}`` shape) or ``csv``
    (the Performance export as text, header row included). Nothing is fetched
    from Search Console and nothing is stored.

    Optional keyword args are sent as-is: ``min_impressions`` (default 50),
    ``target_position`` (1-10, default 5), ``limit`` (default 25, max 200),
    ``exclude_terms``, ``ctr_curve``. Works on every plan; counts as one audit.
    """
    if rows is None and csv is None:
        raise ValueError("Pass rows (a list of dicts) or csv (the export as text)")
    body: dict = dict(options)
    if rows is not None:
        body["rows"] = rows
    if csv is not None:
        body["csv"] = csv
    return _send("post", "/quick-wins", api_key, body)


def backlinks(domain: str, api_key: str, limit: int = 50) -> dict:
    """Observed backlinks for a domain (Basic plan or higher).

    An audit-fed sample, not a comprehensive backlink index: see ``data_caveat``
    in the response. ``limit`` is 1-500.
    """
    return _get("/backlinks", api_key, {"domain": domain, "limit": limit}).json()


def generate_llms_txt(domain: str, api_key: Optional[str] = None) -> str:
    """Generate an llms.txt file for a domain. Returns the file's text.

    Works without a key (basic version). With a key on the Basic plan or higher
    it returns the curated version with per-page descriptions.
    """
    return _get("/llms-generator", api_key, {"domain": domain}).text


# --- GEO (Basic plan or higher) ------------------------------------------------

def geo_audit(url: str, api_key: str) -> dict:
    """Run a GEO (Generative Engine Optimization) audit: how visible the page is
    to LLMs. Basic plan or higher; uses the plan's monthly GEO allowance."""
    return _get("/geo/audit", api_key, {"url": url}).json()


def geo_brand_probe(
    brand: str,
    domain: str,
    prompts: list[str],
    api_key: str,
    models: Optional[list[str]] = None,
    runs_per_prompt: Optional[int] = None,
) -> dict:
    """Probe LLMs to measure how often your brand is mentioned in AI responses
    (Basic plan or higher). ``models`` and ``runs_per_prompt`` (server default 3)
    are optional."""
    body: dict = {"brand": brand, "domain": domain, "prompts": prompts}
    if models is not None:
        body["models"] = models
    if runs_per_prompt is not None:
        body["runs_per_prompt"] = runs_per_prompt
    return _send("post", "/geo/brand-probe", api_key, body)


def add_geo_monitor(
    url: str,
    api_key: str,
    frequency: str = "weekly",
    alert_threshold: int = -5,
    webhook_url: Optional[str] = None,
) -> dict:
    """Create a GEO monitor for a URL (Basic plan or higher).

    ``frequency`` is ``"daily"`` or ``"weekly"`` (the Basic plan runs weekly).
    """
    body: dict = {"url": url, "frequency": frequency, "alert_threshold": alert_threshold}
    if webhook_url:
        body["webhook_url"] = webhook_url
    return _send("post", "/geo/monitor", api_key, body)


def remove_geo_monitor(url: str, api_key: str) -> dict:
    """Remove a GEO monitor (``DELETE /geo/monitor``)."""
    return _send("delete", "/geo/monitor", api_key, {"url": url})


def list_geo_monitors(api_key: str) -> list:
    """List your active GEO monitors."""
    return _get("/geo/monitors", api_key).json()["monitors"]


def geo_monitor_history(monitor_id: int, api_key: str, page: int = 1, per_page: int = 20) -> dict:
    """Score history for a GEO monitor (``per_page`` 1-100)."""
    return _get(f"/geo/monitor/{monitor_id}/history", api_key, {"page": page, "per_page": per_page}).json()


# --- Site crawl (Pro/Ultra, or a Deep Audit credit) ------------------------------

def start_crawl(url: str, api_key: str, max_pages: Optional[int] = None) -> dict:
    """Start a multi-page crawl of one site. Asynchronous: returns
    ``{"job_id", "status", "max_pages", "poll", "site_map"}``; poll it with
    :func:`get_crawl` or block on it with :func:`wait_for_crawl`.

    Follows same-site links plus the sitemap up to your page cap and reports
    broken pages, redirects, duplicate titles and headings, pages missing a title
    or heading, orphan pages and slow pages. ``max_pages`` (1-100) asks for fewer
    pages than the plan's cap. A failed crawl is not counted.
    """
    body: dict = {"url": url}
    if max_pages is not None:
        body["max_pages"] = max_pages
    return _send("post", "/crawl", api_key, body)


def get_crawl(job_id: str, api_key: str) -> dict:
    """Poll a site crawl. ``status`` is ``queued``, ``running``, ``completed`` or
    ``failed``; ``pages_done`` counts up while running; ``result`` holds
    ``summary``, ``issues``, ``pages`` and ``links`` once completed. Only the key
    that started a crawl can read it."""
    return _get(f"/crawl/{job_id}", api_key).json()


def wait_for_crawl(
    job_id: str,
    api_key: str,
    *,
    poll_interval: float = 5.0,
    timeout: float = 600.0,
    on_progress: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Poll an existing crawl until it finishes; return the completed job
    (``result``, ``site_map``, ``pages_done``, ...).

    Raises ``TimeoutError`` if it isn't done within ``timeout`` seconds, or
    ``RuntimeError`` if the crawl fails.
    """
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("Timed out waiting for crawl to complete")
        job = get_crawl(job_id, api_key)
        if on_progress:
            on_progress(job)
        state = job.get("status")
        if state == "completed":
            return job
        if state == "failed":
            raise RuntimeError(job.get("error") or "Crawl failed")
        time.sleep(poll_interval)


def crawl(
    url: str,
    api_key: str,
    max_pages: Optional[int] = None,
    *,
    poll_interval: float = 5.0,
    timeout: float = 600.0,
    on_progress: Optional[Callable[[dict], None]] = None,
) -> dict:
    """Start a site crawl and block until it finishes; return the completed job
    (see :func:`wait_for_crawl`)."""
    job = start_crawl(url, api_key, max_pages)
    return wait_for_crawl(job["job_id"], api_key, poll_interval=poll_interval, timeout=timeout, on_progress=on_progress)


# --- AI citations (Starter plan or higher) ---------------------------------------
#
# A check is one prompt on one engine, sampled once. Every plan has a monthly
# allowance of checks; top-up checks are spent only after it.

def citation_starter_prompts(
    topic: str,
    api_key: str,
    *,
    brand: Optional[str] = None,
    competitors=None,
    audience: Optional[str] = None,
    features=None,
    use_cases=None,
    per_category: Optional[int] = None,
    limit: Optional[int] = None,
) -> dict:
    """A starter set of prompts to track, built from fixed templates.

    ``competitors`` (up to 5), ``features`` and ``use_cases`` (up to 6 each)
    take a list or a comma-separated string. Returns ``prompts`` (flat list,
    ready for :func:`create_citation_tracker`), ``categories`` and ``items``.
    Works on every plan, is not metered and spends no AI check.
    """
    params = _params(
        topic=topic, brand=brand, competitors=_csv(competitors), audience=audience,
        features=_csv(features), use_cases=_csv(use_cases), per_category=per_category, limit=limit,
    )
    return _get("/citations/prompts/starter", api_key, params).json()


def citation_suggest_prompts(domain: str, api_key: str) -> dict:
    """Suggest prompts to track, read off what the site says it does."""
    return _get("/citations/prompts/suggest", api_key, {"domain": domain}).json()


def create_citation_tracker(brand: str, api_key: str, **fields) -> dict:
    """Track a brand's visibility in AI answers (Starter plan or higher).

    Keyword args are sent to the API as-is: ``domains``, ``prompts``,
    ``competitors``, ``engines`` (``chatgpt``, ``gemini``, ``perplexity``,
    ``claude``), ``samples``, ``cadence`` (``daily`` | ``weekly`` | ``monthly`` |
    ``manual``), ``webhook_url`` (https). With no prompts yet, leave ``prompts``
    out and pass ``starter={"topic": "...", "audience": "..."}``; the response's
    ``starter`` block says what was generated and kept.
    """
    return _send("post", "/citations/trackers", api_key, {"brand": brand, **fields})


def list_citation_trackers(api_key: str) -> dict:
    """List this key's citation trackers: ``{"trackers": [...], "usage": {...}}``.

    ``usage`` holds the month's ``checks_limit`` / ``checks_used`` /
    ``checks_remaining``, the top-up balance (``topup_checks_remaining``) and
    ``checks_available``, what a run can spend now.
    """
    return _get("/citations/trackers", api_key).json()


def get_citation_tracker(tracker_id: int, api_key: str) -> dict:
    """Read one citation tracker."""
    return _get(f"/citations/trackers/{tracker_id}", api_key).json()


def update_citation_tracker(tracker_id: int, api_key: str, **fields) -> dict:
    """Edit a tracker's ``prompts``, ``engines``, ``competitors``, ``samples``,
    ``cadence`` or ``webhook_url`` (only the fields you pass change)."""
    return _send("patch", f"/citations/trackers/{tracker_id}", api_key, fields)


def delete_citation_tracker(tracker_id: int, api_key: str) -> dict:
    """Stop tracking a brand. Run history is kept until its retention expires."""
    return _send("delete", f"/citations/trackers/{tracker_id}", api_key)


def run_citation_tracker(tracker_id: int, api_key: str) -> dict:
    """Run a tracker now and return the run summary. Every prompt x engine x
    sample counts as one check.

    A run needs all of its checks up front (the month's remaining allowance plus
    any top-up balance); if that is short it is refused with 429 and nothing is
    spent. The request stays open while the engines answer, so it can take a while.
    """
    return _send("post", f"/citations/trackers/{tracker_id}/run", api_key)


def get_citation_run(run_id: int, api_key: str) -> dict:
    """Run status plus every per-prompt, per-engine result."""
    return _get(f"/citations/runs/{run_id}", api_key).json()


def citation_tracker_history(tracker_id: int, api_key: str, days: int = 90) -> dict:
    """Timeseries of mention rate, citation rate, share of voice and average
    position (``days`` 1-365)."""
    return _get(f"/citations/trackers/{tracker_id}/history", api_key, {"days": days}).json()


def citation_check(brand: str, prompt: str, api_key: str, **fields) -> dict:
    """One-off citation check: no tracker, metered per check (paid plans only).

    Keyword args are sent as-is: ``domains``, ``engines``, ``samples``
    (default 1), ``competitors``.
    """
    return _send("post", "/citations/check", api_key, {"brand": brand, "prompt": prompt, **fields})


def citation_topups(api_key: str) -> dict:
    """Top-up packs for AI citation checks and this account's balance
    (``packs``, ``can_buy``, ``balance``, ``next_expiry``, ``monthly``,
    ``checks_available``, ``grants``)."""
    return _get("/citations/topups", api_key).json()


def citation_topup_checkout(pack: str, api_key: str) -> str:
    """Start a one-time Stripe Checkout for top-up checks (paid plans only).

    ``pack`` is the ``key`` of one of ``citation_topups()["packs"]`` (``"500"``
    or ``"2000"`` checks). Returns the
    checkout URL: open it to pay by card. Nothing is charged by this call; the
    checks are added when the payment completes.
    """
    return _send("post", "/citations/topups/checkout", api_key, {"pack": str(pack)})["url"]


def citation_auto_reload(api_key: str) -> dict:
    """Read the auto-reload setting for AI citation checks and this month's use.

    Read-only by design: auto-reload can only be turned on or changed from the
    dashboard (signed in), never with an API key, because turning it on
    authorizes charges. There is no setter in this client.
    """
    return _get("/citations/auto-reload", api_key).json()


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

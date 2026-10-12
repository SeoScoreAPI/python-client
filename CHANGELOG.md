# Changelog

## 1.7.1 (2026-10-09)

Package metadata only: the repository and issue links point at the public
`SeoScoreAPI` repositories. No code changes.

## 1.7.0 (2026-10-07)

Core Web Vitals are now opt-in on the API, so audits no longer wait on Google
PageSpeed Insights unless you ask:

- `audit(url, api_key, cwv=False)`: pass `cwv=True` to get measured LCP, INP, CLS, FCP
  and TTFB under `core_web_vitals` in the same response. The first measurement of a URL
  adds about 10 seconds; it is cached for 24 hours.
- `batch_audit(urls, api_key, cwv=False)`: the same for every URL in the batch.
- Without `cwv=True`, `core_web_vitals["status"]` is `"not_requested"` (metrics `None`),
  unless a measurement of that URL is already cached, which is returned as before.
- Nothing else changed; existing calls behave as they did, only faster.

## 1.6.1 (2026-10-07)

Fixes signup, which has been a two-step flow on the API for some time:

- `signup(email)` no longer raises `KeyError` after the verification email is sent.
  It returns the API's response (`{"status": "verification_required", "message": ...}`)
  instead of a key. `POST /signup` does not issue a key any more.
- New `verify(email, code)`: sends the emailed 6-digit code to `POST /verify` and
  returns the API key. Raises `requests.HTTPError` (400) on a wrong or expired code.
- README: the two-step signup, with an example.

## 1.6.0 (2026-10-06)

Catches the client up with the API. New functions, no changes to existing ones:

- Accessibility and reports: `accessibility_audit` (`GET /audit/accessibility`),
  `audit_export` (`GET /audit/export`, returns the PDF / Markdown / CSV as `bytes`).
- Single-page analyses: `ai_readability`, `trackers`, `conversion`, `quick_wins`
  (`POST /quick-wins`), `backlinks`, `generate_llms_txt` (returns `str`; key optional).
- GEO: `geo_audit`, `geo_brand_probe`, `add_geo_monitor`, `remove_geo_monitor`,
  `list_geo_monitors`, `geo_monitor_history`.
- Site crawl: `start_crawl`, `get_crawl`, `wait_for_crawl`, `crawl` (start and wait).
- AI citations: `citation_starter_prompts`, `citation_suggest_prompts`,
  `create_citation_tracker`, `list_citation_trackers`, `get_citation_tracker`,
  `update_citation_tracker`, `delete_citation_tracker`, `run_citation_tracker`,
  `get_citation_run`, `citation_tracker_history`, `citation_check`, `citation_topups`,
  `citation_topup_checkout` (returns the Stripe Checkout URL), `citation_auto_reload`
  (read-only: the API has no way to turn auto-reload on, and neither does this client).
- `remove_monitor` (`DELETE /monitors`).
- Tests for all of the above (`tests/test_endpoints.py`).

## 1.5.0 (2026-10-02)

- Deep Site Audit calls go to the main host, `https://seoscoreapi.com`
  (`POST /site-audit`, `GET /site-audit/{job_id}`, `GET /deep-audit/usage`), instead
  of `engine.seoscoreapi.com`. The old host still works.
- Base-URL override for Deep Audit: `base_url=` on every Deep Audit function, the
  module attribute `DEEP_AUDIT_URL`, or the `SEOSCORE_DEEP_AUDIT_URL` env var.
- New `wait_for_site_audit(job_id, api_key, ...)`: poll an existing job to completion.
- New `deep_audit_usage(api_key)`. `engine_usage()` stays as an alias (on the main host it
  now calls `/deep-audit/usage`, since `/usage` there is the per-URL audit allowance).
- Tests for the Deep Audit client (`tests/`, run with `pytest`).

## 1.4.0

- Deep Audit: `site_audit`, `get_site_audit`, `deep_audit`, `engine_usage` (engine host).

Earlier releases: see the git history of `sdks/python`.

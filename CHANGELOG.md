# Changelog

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

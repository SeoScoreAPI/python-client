# seoscoreapi

Python client for [SEO Score API](https://seoscoreapi.com) — audit any URL for SEO issues with one function call.

## Install

```bash
pip install seoscoreapi
```

## Quick Start

```python
import os
from seoscoreapi import audit

# Get a free API key (2 audits/day, no credit card) at https://seoscoreapi.com/#signup
key = os.environ["SEO_SCORE_API_KEY"]

# Run an audit
result = audit("https://example.com", api_key=key)
print(f"Score: {result['score']}/100 ({result['grade']})")
```

## Functions

| Function | Description |
|---|---|
| `signup(email)` | Starts signup: the API emails a 6-digit code. It does not return a key (known issue: this call raises `KeyError` after the code is sent). Finish at [seoscoreapi.com](https://seoscoreapi.com/#signup) or with `POST /verify` |
| `audit(url, api_key)` | Run SEO audit on a URL |
| `batch_audit(urls, api_key)` | Audit up to 10 URLs in one call (paid) |
| `compare(urls, api_key)` | Compare 2–5 URLs with a structured diff (Basic+) |
| `competitive_audit(url, competitor_url, keyword, api_key)` | Head-to-head audit with gap score (Pro+) |
| `history(url, api_key, limit=100, since=None)` | Full audit timeseries + summary for a URL (Starter+) |
| `history_domains(api_key)` | Every domain audited by this key with latest score and 30-day trend (Starter+) |
| `usage(api_key)` | Check usage and limits |
| `add_monitor(url, api_key, frequency="daily", webhook_url=None, alert_threshold=5)` | Set up score monitoring with optional Slack/webhook alerts (paid) |
| `list_monitors(api_key)` | List active monitors |
| `scoreboard_opt_out(api_key, opt_out=True)` | Opt in or out of the public scoreboard |
| `report_url(domain)` | Get shareable report URL |

## Historical tracking

Every audit on a paid plan returns a `history` block on the `/audit` response:

```python
result = audit("https://example.com", api_key=key)
delta = result["history"].get("delta")
if delta:
    print(f"Score change: {delta['score']:+.1f} ({delta.get('grade_change') or 'no grade change'})")
```

Pull the full timeseries with `history()` or a one-shot per-domain summary with `history_domains()`. Retention windows: Starter 30 days, Basic 90 days, Pro 1 year, Ultra unlimited.

## Webhook alerts on score drops

```python
add_monitor(
    "https://example.com",
    api_key=key,
    frequency="daily",
    webhook_url="https://hooks.slack.com/services/T0/B0/xxxx",
    alert_threshold=5,
)
```

Slack incoming-webhook URLs are auto-formatted as Block Kit messages; any other https endpoint receives the raw event JSON.

## Deep Site Audit (Pro/Ultra, or credits)

A deep, AI-assisted audit scoring a URL across 9 dimensions (thousands of catalog
checks plus up to 150 AI checks). It runs asynchronously, so start a job and poll it,
or use `deep_audit` to block for the result:

```python
import seoscoreapi as seo

# One call, waits for the result (handles the queue + backpressure for you):
result = seo.deep_audit(
    "https://yoursite.com", API_KEY,
    business_type="saas",                      # tunes which checks apply
    on_progress=lambda s: print(s["status"], s.get("queue_position", s.get("progress"))),
)
print(result["scores"]["lai_score"], result["scores"]["section_scores"])

# Or drive the job yourself:
job = seo.site_audit("https://yoursite.com", API_KEY)       # POST /site-audit
status = seo.get_site_audit(job["job_id"], API_KEY)         # GET  /site-audit/{job_id}
# status["status"] -> queued | running | completed | failed
#   queued    -> {"queue_position", "eta_seconds"}
#   completed -> {"result"}
result = seo.wait_for_site_audit(job["job_id"], API_KEY, timeout=600)

seo.deep_audit_usage(API_KEY)   # GET /deep-audit/usage -> {"site_audit": {"used", "remaining"}, ...}
```

Deep audits are included on **Pro** ($39/mo, 20/mo) and **Ultra** ($99/mo, 100/mo);
any other key can run them on purchased credits.

Since 1.5.0 the SDK calls the main host, `https://seoscoreapi.com`, like every other
endpoint. To point Deep Audit somewhere else (a proxy, staging, or the legacy
`engine.seoscoreapi.com` host, which still works), pass `base_url=` to any Deep Audit
function, assign `seoscoreapi.DEEP_AUDIT_URL`, or set `SEOSCORE_DEEP_AUDIT_URL`.
`engine_usage()` is kept as an alias of `deep_audit_usage()`.

Docs: [seoscoreapi.com/docs](https://seoscoreapi.com/docs) (Deep Site Audit section).

## Full Documentation

[seoscoreapi.com/docs](https://seoscoreapi.com/docs)

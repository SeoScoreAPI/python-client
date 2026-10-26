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

# Get a free API key (20 audits a month, no credit card) at https://seoscoreapi.com/#signup
key = os.environ["SEO_SCORE_API_KEY"]

# Run an audit
result = audit("https://example.com", api_key=key)
print(f"Score: {result['score']}/100 ({result['grade']})")
```

## Functions

| Function | Description |
|---|---|
| `signup(email)` | Start signup: the API emails a 6-digit code. Returns the API's response (`{"status": "verification_required", ...}`), not a key |
| `verify(email, code)` | Finish signup with the emailed code. Returns the API key (shown only once) |
| `audit(url, api_key, cwv=False)` | Run SEO audit on a URL. `cwv=True` adds measured Core Web Vitals (slower, see below) |
| `batch_audit(urls, api_key, cwv=False)` | Audit up to 10 URLs in one call (paid). `cwv=True` adds Core Web Vitals to each |
| `compare(urls, api_key)` | Compare 2–5 URLs with a structured diff (Basic+) |
| `competitive_audit(url, competitor_url, keyword, api_key)` | Head-to-head audit with gap score (Pro+) |
| `history(url, api_key, limit=100, since=None)` | Full audit timeseries + summary for a URL (Starter+) |
| `history_domains(api_key)` | Every domain audited by this key with latest score and 30-day trend (Starter+) |
| `usage(api_key)` | Check usage and limits |
| `add_monitor(url, api_key, frequency="daily", webhook_url=None, alert_threshold=5)` | Set up score monitoring with optional Slack/webhook alerts (paid) |
| `list_monitors(api_key)` | List active monitors |
| `remove_monitor(url, api_key)` | Remove a monitor |
| `scoreboard_opt_out(api_key, opt_out=True)` | Opt in or out of the public scoreboard |
| `report_url(domain)` | Get shareable report URL |
| `accessibility_audit(url, api_key, include=None)` | ADA / WCAG 2.1 AA audit (paid; own monthly allowance). `include="trackers"` adds the tracker inventory |
| `audit_export(url, api_key, format="pdf", brand_name=None, brand_color=None, logo_url=None)` | Audit as a PDF / Markdown / CSV file; returns `bytes`. White-label on Pro and Ultra |
| `ai_readability(url, api_key)` | How well AI/LLM systems can consume the page |
| `trackers(url, api_key)` | Third-party trackers and pixels the page loads |
| `conversion(url, api_key, page_type=None)` | Conversion score: headline, CTA, trust, forms, objections |
| `quick_wins(api_key, rows=None, csv=None, **options)` | Page-2 quick wins from your own Search Console export (every plan) |
| `backlinks(domain, api_key, limit=50)` | Observed backlinks, an audit-fed sample (Basic+) |
| `generate_llms_txt(domain, api_key=None)` | llms.txt for a domain; returns `str`. Curated version on Basic+ |
| `geo_audit(url, api_key)` | GEO audit: visibility to LLMs (Basic+) |
| `geo_brand_probe(brand, domain, prompts, api_key, models=None, runs_per_prompt=None)` | How often LLMs mention your brand (Basic+) |
| `add_geo_monitor(url, api_key, frequency="weekly", alert_threshold=-5, webhook_url=None)` | Create a GEO monitor (Basic+) |
| `list_geo_monitors(api_key)` / `remove_geo_monitor(url, api_key)` | List / remove GEO monitors |
| `geo_monitor_history(monitor_id, api_key, page=1, per_page=20)` | Score history for a GEO monitor |
| `start_crawl(url, api_key, max_pages=None)` / `get_crawl(job_id, api_key)` | Start / poll a multi-page site crawl (Pro/Ultra, or a Deep Audit credit) |
| `wait_for_crawl(job_id, api_key, ...)` / `crawl(url, api_key, max_pages=None, ...)` | Poll a crawl to completion / start one and wait |
| `citation_starter_prompts(topic, api_key, ...)` / `citation_suggest_prompts(domain, api_key)` | Prompts to track for AI citations (not metered) |
| `create_citation_tracker(brand, api_key, **fields)` | Track a brand in AI answers (Starter+) |
| `list_citation_trackers(api_key)` / `get_citation_tracker(id, api_key)` | Trackers plus the month's check usage / one tracker |
| `update_citation_tracker(id, api_key, **fields)` / `delete_citation_tracker(id, api_key)` | Edit / stop a tracker |
| `run_citation_tracker(id, api_key)` / `get_citation_run(run_id, api_key)` | Run a tracker now / read a run's results |
| `citation_tracker_history(id, api_key, days=90)` | Mention rate, citation rate, share of voice, position over time |
| `citation_check(brand, prompt, api_key, **fields)` | One-off citation check, metered per check (paid) |
| `citation_topups(api_key)` / `citation_topup_checkout(pack, api_key)` | Top-up packs and balance / Stripe Checkout URL for a pack |
| `citation_auto_reload(api_key)` | Read the auto-reload setting (read-only; change it on the dashboard) |

Errors are `requests.HTTPError` (from `raise_for_status()`); the API's message is in
`err.response.json()["detail"]`.

## Get an API key from code

Signup takes two calls. `signup()` emails a 6-digit code (valid for 10 minutes) and
`verify()` trades that code for the key. You can also sign up at
[seoscoreapi.com](https://seoscoreapi.com/#signup).

```python
import requests
from seoscoreapi import signup, verify

email = "you@example.com"
print(signup(email)["message"])  # "Check your email for a 6-digit verification code."

try:
    key = verify(email, input("Code from the email: "))
except requests.HTTPError as e:
    raise SystemExit(e.response.json()["detail"])  # wrong or expired code

print(key)  # save it: the key is shown only once
```

`signup()` raises `requests.HTTPError` when the address is refused (400) or already
has an active key (409). `verify()` raises it (400) on a wrong or expired code; five
wrong codes void the signup, so call `signup()` again.

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

## Core Web Vitals (opt-in)

Audits are fast because they do not wait on Google PageSpeed Insights. Ask for measured
Core Web Vitals when you need them:

```python
result = audit("https://example.com", api_key=key, cwv=True)
vitals = result["core_web_vitals"]
if vitals["status"] == "ok":
    print(vitals["lcp_ms"], vitals["inp_ms"], vitals["cls"], vitals["source"])  # source: "field" or "lab"
elif vitals.get("pending"):
    print("Still measuring; audit this URL again in a minute")
else:
    print("No Core Web Vitals:", vitals.get("reason"))
```

The first measurement of a URL adds about 10 seconds (the API waits up to 25); it is
cached for 24 hours, so repeats are instant. It works on every plan and never changes the
score. Without `cwv=True` the block reads `{"status": "not_requested", ...}` with the
metrics set to `None`.

## Accessibility audit and report files

```python
import seoscoreapi as seo

ada = seo.accessibility_audit("https://example.com", API_KEY)
print(ada["score"], len(ada["violations"]))

# PDF, Markdown ("md") or CSV. Returns the file's bytes.
pdf = seo.audit_export("https://example.com", API_KEY, "pdf", brand_name="Acme Agency")
open("report.pdf", "wb").write(pdf)
```

ADA audits are on paid plans and have their own monthly allowance, separate from the
audit quota (`usage()` reports `ada_remaining`). `audit_export` counts as one audit; the
white-label parameters need Pro or Ultra.

## Site crawl

Asynchronous, like Deep Site Audit. Pro and Ultra include crawls; any other plan spends
one Deep Audit credit per crawl.

```python
job = seo.crawl("https://example.com", API_KEY, max_pages=25,
                on_progress=lambda j: print(j["status"], j.get("pages_done")))
print(job["result"]["summary"], job["site_map"])

# Or drive it yourself:
started = seo.start_crawl("https://example.com", API_KEY)     # POST /crawl
job = seo.get_crawl(started["job_id"], API_KEY)               # GET  /crawl/{job_id}
job = seo.wait_for_crawl(started["job_id"], API_KEY, timeout=600)
```

`wait_for_crawl` and `crawl` return the whole completed job (`result`, `site_map`,
`pages_done`), raise `TimeoutError` on timeout and `RuntimeError` if the crawl fails.

## AI citations

Do ChatGPT, Gemini, Perplexity and Claude mention and cite you? A tracker is a brand plus
the prompts buyers type. A check is one prompt on one engine, sampled once.

```python
starter = seo.citation_starter_prompts("SEO audit API", API_KEY, brand="Acme",
                                       competitors=["Rival"], audience="marketing agencies")

tracker = seo.create_citation_tracker("Acme", API_KEY, domains=["acme.com"],
                                      prompts=starter["prompts"], cadence="weekly")
run = seo.run_citation_tracker(tracker["id"], API_KEY)        # waits for the engines
history = seo.citation_tracker_history(tracker["id"], API_KEY, days=90)

seo.list_citation_trackers(API_KEY)["usage"]   # checks_limit, checks_used, checks_available, ...
seo.citation_topups(API_KEY)                   # packs, balance, can_buy
url = seo.citation_topup_checkout("500", API_KEY)   # Stripe Checkout URL; nothing is charged until it is paid
seo.citation_auto_reload(API_KEY)              # read-only
```

A run needs all of its checks up front (the month's allowance plus any top-up balance);
if that is short the API answers 429 and nothing is spent. Auto-reload can only be turned
on or changed from the dashboard, never with an API key, so this client has no setter.

## Search Console quick wins

```python
wins = seo.quick_wins(API_KEY, csv=open("Queries.csv").read(), exclude_terms=["acme"])
for w in wins["quick_wins"]:
    print(w["query"], w["position"], w["estimated_extra_clicks"])
```

We do not connect to your Search Console: you send the export (or `rows=[...]`).

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

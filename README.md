# seoscoreapi

Python client for [SEO Score API](https://seoscoreapi.com) — audit any URL for SEO issues with one function call.

## Install

```bash
pip install seoscoreapi
```

## Quick Start

```python
from seoscoreapi import audit, signup

# Get a free API key (2 audits/day)
key = signup("you@example.com")

# Audit any URL
result = audit("https://example.com", api_key=key)
print(f"Score: {result['score']}/100 ({result['grade']})")

# See what to fix
for p in result["priorities"]:
    print(f"  [{p['severity']}] {p['issue']}")
```

## Functions

| Function | Description |
|----------|-------------|
| `signup(email)` | Get a free API key |
| `audit(url, api_key)` | Run SEO audit on a URL |
| `batch_audit(urls, api_key)` | Audit multiple URLs (paid) |
| `usage(api_key)` | Check your usage/limits |
| `add_monitor(url, api_key)` | Set up score monitoring (paid) |
| `list_monitors(api_key)` | List active monitors |
| `scoreboard_opt_out(api_key)` | Opt in/out of public scoreboard |
| `report_url(domain)` | Get shareable report URL |

## What Gets Checked

28 checks across 5 categories: meta & content, technical SEO, social/OG, performance, accessibility.

## Links

- [Website & Live Demo](https://seoscoreapi.com)
- [API Docs](https://seoscoreapi.com/docs)
- [GitHub Action](https://github.com/SeoScoreAPI/seo-audit-action)

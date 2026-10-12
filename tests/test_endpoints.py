"""Tests for the endpoint wrappers added in 1.6.0. No network: requests.* is patched."""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import seoscoreapi as seo  # noqa: E402

B = "https://seoscoreapi.com"


class FakeResponse:
    def __init__(self, payload=None, status=200, content=b"", text=""):
        self._payload = {} if payload is None else payload
        self.status_code = status
        self.content = content
        self.text = text
        self.headers = {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise seo.requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(seo.time, "sleep", lambda s: None)


def patched(method, payload=None, **kw):
    return mock.patch.object(seo.requests, method, return_value=FakeResponse(payload, **kw))


# (call, HTTP method, path, expected query params)
GETS = [
    (lambda: seo.accessibility_audit("https://e.com", "k"), "/audit/accessibility", {"url": "https://e.com"}),
    (lambda: seo.accessibility_audit("https://e.com", "k", include="trackers"), "/audit/accessibility",
     {"url": "https://e.com", "include": "trackers"}),
    (lambda: seo.ai_readability("https://e.com", "k"), "/ai-readability", {"url": "https://e.com"}),
    (lambda: seo.trackers("https://e.com", "k"), "/trackers", {"url": "https://e.com"}),
    (lambda: seo.conversion("https://e.com", "k"), "/conversion", {"url": "https://e.com"}),
    (lambda: seo.conversion("https://e.com", "k", page_type="saas"), "/conversion",
     {"url": "https://e.com", "page_type": "saas"}),
    (lambda: seo.backlinks("e.com", "k", limit=10), "/backlinks", {"domain": "e.com", "limit": 10}),
    (lambda: seo.geo_audit("https://e.com", "k"), "/geo/audit", {"url": "https://e.com"}),
    (lambda: seo.geo_monitor_history(7, "k", page=2), "/geo/monitor/7/history", {"page": 2, "per_page": 20}),
    (lambda: seo.get_crawl("a" * 32, "k"), "/crawl/" + "a" * 32, None),
    (lambda: seo.citation_suggest_prompts("e.com", "k"), "/citations/prompts/suggest", {"domain": "e.com"}),
    (lambda: seo.list_citation_trackers("k"), "/citations/trackers", None),
    (lambda: seo.get_citation_tracker(3, "k"), "/citations/trackers/3", None),
    (lambda: seo.get_citation_run(9, "k"), "/citations/runs/9", None),
    (lambda: seo.citation_tracker_history(3, "k", days=30), "/citations/trackers/3/history", {"days": 30}),
    (lambda: seo.citation_topups("k"), "/citations/topups", None),
    (lambda: seo.citation_auto_reload("k"), "/citations/auto-reload", None),
]


@pytest.mark.parametrize("call,path,params", GETS)
def test_get_wrappers(call, path, params):
    with patched("get", {"ok": 1}) as get:
        assert call() == {"ok": 1}
    args, kwargs = get.call_args
    assert args[0] == B + path
    assert kwargs["params"] == params
    assert kwargs["headers"]["X-API-Key"] == "k"
    assert kwargs["headers"]["User-Agent"] == f"seoscoreapi-python/{seo.__version__}"


# (call, requests function, path, expected JSON body)
SENDS = [
    (lambda: seo.remove_monitor("https://e.com", "k"), "delete", "/monitors", {"url": "https://e.com"}),
    (lambda: seo.geo_brand_probe("Acme", "acme.com", ["best crm"], "k"), "post", "/geo/brand-probe",
     {"brand": "Acme", "domain": "acme.com", "prompts": ["best crm"]}),
    (lambda: seo.geo_brand_probe("Acme", "acme.com", ["p"], "k", models=["claude"], runs_per_prompt=2), "post",
     "/geo/brand-probe", {"brand": "Acme", "domain": "acme.com", "prompts": ["p"], "models": ["claude"], "runs_per_prompt": 2}),
    (lambda: seo.add_geo_monitor("https://e.com", "k"), "post", "/geo/monitor",
     {"url": "https://e.com", "frequency": "weekly", "alert_threshold": -5}),
    (lambda: seo.add_geo_monitor("https://e.com", "k", webhook_url="https://h.example/x"), "post", "/geo/monitor",
     {"url": "https://e.com", "frequency": "weekly", "alert_threshold": -5, "webhook_url": "https://h.example/x"}),
    (lambda: seo.remove_geo_monitor("https://e.com", "k"), "delete", "/geo/monitor", {"url": "https://e.com"}),
    (lambda: seo.start_crawl("https://e.com", "k"), "post", "/crawl", {"url": "https://e.com"}),
    (lambda: seo.start_crawl("https://e.com", "k", max_pages=10), "post", "/crawl", {"url": "https://e.com", "max_pages": 10}),
    (lambda: seo.quick_wins("k", rows=[{"query": "q", "position": 11.4}], limit=5), "post", "/quick-wins",
     {"rows": [{"query": "q", "position": 11.4}], "limit": 5}),
    (lambda: seo.quick_wins("k", csv="Query,Clicks\nq,1"), "post", "/quick-wins", {"csv": "Query,Clicks\nq,1"}),
    (lambda: seo.create_citation_tracker("Acme", "k", domains=["acme.com"], starter={"topic": "CRM"}), "post",
     "/citations/trackers", {"brand": "Acme", "domains": ["acme.com"], "starter": {"topic": "CRM"}}),
    (lambda: seo.update_citation_tracker(3, "k", cadence="monthly"), "patch", "/citations/trackers/3", {"cadence": "monthly"}),
    (lambda: seo.delete_citation_tracker(3, "k"), "delete", "/citations/trackers/3", None),
    (lambda: seo.run_citation_tracker(3, "k"), "post", "/citations/trackers/3/run", None),
    (lambda: seo.citation_check("Acme", "best crm", "k", engines=["chatgpt"]), "post", "/citations/check",
     {"brand": "Acme", "prompt": "best crm", "engines": ["chatgpt"]}),
]


@pytest.mark.parametrize("call,method,path,body", SENDS)
def test_body_wrappers(call, method, path, body):
    with patched(method, {"ok": 1}) as send:
        assert call() == {"ok": 1}
    args, kwargs = send.call_args
    assert args[0] == B + path
    assert kwargs["json"] == body
    assert kwargs["headers"]["X-API-Key"] == "k"


def test_audit_export_returns_bytes_and_sends_white_label_params():
    with patched("get", content=b"%PDF-1.7") as get:
        data = seo.audit_export("https://e.com", "k", brand_name="Acme", brand_color="#112233")
    assert data == b"%PDF-1.7"
    assert get.call_args[0][0] == B + "/audit/export"
    assert get.call_args[1]["params"] == {
        "url": "https://e.com", "format": "pdf", "brand_name": "Acme", "brand_color": "#112233"}


def test_audit_export_other_formats():
    with patched("get", content=b"# Report") as get:
        assert seo.audit_export("https://e.com", "k", "md") == b"# Report"
    assert get.call_args[1]["params"]["format"] == "md"


def test_generate_llms_txt_is_text_and_key_is_optional():
    with patched("get", text="# Example\n") as get:
        assert seo.generate_llms_txt("e.com") == "# Example\n"
    assert get.call_args[0][0] == B + "/llms-generator"
    assert "X-API-Key" not in get.call_args[1]["headers"]
    with patched("get", text="x") as get:
        seo.generate_llms_txt("e.com", "k")
    assert get.call_args[1]["headers"]["X-API-Key"] == "k"


def test_list_geo_monitors_unwraps():
    with patched("get", {"monitors": [{"id": 1}]}):
        assert seo.list_geo_monitors("k") == [{"id": 1}]


def test_starter_prompts_joins_lists_and_drops_unset():
    with patched("get", {"prompts": []}) as get:
        seo.citation_starter_prompts("CRM", "k", brand="Acme", competitors=["A", "B"], features="x, y", limit=15)
    assert get.call_args[0][0] == B + "/citations/prompts/starter"
    assert get.call_args[1]["params"] == {
        "topic": "CRM", "brand": "Acme", "competitors": "A,B", "features": "x, y", "limit": 15}


def test_topup_checkout_returns_the_url():
    with patched("post", {"url": "https://checkout.stripe.com/c/x"}) as post:
        assert seo.citation_topup_checkout(500, "k") == "https://checkout.stripe.com/c/x"
    assert post.call_args[0][0] == B + "/citations/topups/checkout"
    assert post.call_args[1]["json"] == {"pack": "500"}


def test_auto_reload_is_read_only():
    names = [n for n in dir(seo) if "auto_reload" in n]
    assert names == ["citation_auto_reload"]


def test_quick_wins_needs_rows_or_csv():
    with pytest.raises(ValueError):
        seo.quick_wins("k")


def test_http_errors_raise():
    with patched("get", status=403):
        with pytest.raises(seo.requests.HTTPError):
            seo.geo_audit("https://e.com", "k")
    with patched("post", status=429):
        with pytest.raises(seo.requests.HTTPError):
            seo.run_citation_tracker(3, "k")


def test_wait_for_crawl_returns_the_completed_job():
    seq = [
        FakeResponse({"status": "queued", "pages_done": 0}),
        FakeResponse({"status": "running", "pages_done": 4}),
        FakeResponse({"status": "completed", "pages_done": 9, "site_map": "m", "result": {"summary": {}}}),
    ]
    seen = []
    with mock.patch.object(seo.requests, "get", side_effect=seq):
        job = seo.wait_for_crawl("abc", "k", on_progress=lambda s: seen.append(s["status"]))
    assert job["result"] == {"summary": {}} and job["site_map"] == "m"
    assert seen == ["queued", "running", "completed"]


def test_wait_for_crawl_failed_and_timeout():
    with patched("get", {"status": "failed", "error": "boom"}):
        with pytest.raises(RuntimeError, match="boom"):
            seo.wait_for_crawl("abc", "k")
    with patched("get", {"status": "running"}):
        with pytest.raises(TimeoutError):
            seo.wait_for_crawl("abc", "k", timeout=0)


def test_crawl_starts_then_polls():
    with patched("post", {"job_id": "abc", "status": "queued"}) as post, \
         patched("get", {"status": "completed", "result": {"ok": 1}}) as get:
        assert seo.crawl("https://e.com", "k", max_pages=5)["result"] == {"ok": 1}
    assert post.call_args[1]["json"] == {"url": "https://e.com", "max_pages": 5}
    assert get.call_args[0][0] == B + "/crawl/abc"


# --- signup is two steps: POST /signup emails a code, POST /verify returns the key

def test_signup_returns_the_verification_response_not_a_key():
    payload = {"status": "verification_required", "message": "Check your email for a 6-digit verification code."}
    with patched("post", payload) as m:
        out = seo.signup("you@example.com")
    assert out == payload
    assert m.call_args.args[0] == f"{B}/signup"
    assert m.call_args.kwargs["json"] == {"email": "you@example.com"}
    assert "X-API-Key" not in m.call_args.kwargs["headers"]


def test_signup_passes_through_a_response_that_carries_a_key():
    with patched("post", {"api_key": "ssa_x", "tier": "free"}):
        assert seo.signup("you@example.com")["api_key"] == "ssa_x"


def test_signup_raises_when_the_email_already_has_a_key():
    with patched("post", {"detail": "Email already has an active key (prefix: ssa_abc...)"}, status=409):
        with pytest.raises(seo.requests.HTTPError):
            seo.signup("you@example.com")


def test_verify_returns_the_api_key():
    payload = {"api_key": "ssa_live_key", "tier": "free", "limits": {}, "message": "Save your API key"}
    with patched("post", payload) as m:
        assert seo.verify("you@example.com", " 012345 ") == "ssa_live_key"
    assert m.call_args.args[0] == f"{B}/verify"
    assert m.call_args.kwargs["json"] == {"email": "you@example.com", "code": "012345"}


def test_verify_accepts_an_integer_code():
    with patched("post", {"api_key": "k"}) as m:
        seo.verify("you@example.com", 123456)
    assert m.call_args.kwargs["json"]["code"] == "123456"


def test_verify_raises_on_a_bad_code():
    with patched("post", {"detail": "Invalid verification code. 4 attempts remaining."}, status=400):
        with pytest.raises(seo.requests.HTTPError):
            seo.verify("you@example.com", "000000")


# --- Core Web Vitals opt-in (1.7.0) -------------------------------------------------

def test_audit_does_not_ask_for_core_web_vitals_by_default():
    with patched("get", {"score": 90}) as get:
        assert seo.audit("https://e.com", "k") == {"score": 90}
    args, kwargs = get.call_args
    assert args[0] == B + "/audit"
    assert kwargs["params"] == {"url": "https://e.com"}
    assert kwargs["headers"]["X-API-Key"] == "k"


def test_audit_cwv_true_sends_the_parameter():
    payload = {"score": 90, "core_web_vitals": {"status": "ok", "lcp_ms": 1800}}
    with patched("get", payload) as get:
        assert seo.audit("https://e.com", "k", cwv=True)["core_web_vitals"]["lcp_ms"] == 1800
    assert get.call_args.kwargs["params"] == {"url": "https://e.com", "cwv": "true"}


def test_audit_cwv_false_is_the_default_request():
    with patched("get", {}) as get:
        seo.audit("https://e.com", "k", cwv=False)
    assert get.call_args.kwargs["params"] == {"url": "https://e.com"}


def test_batch_audit_cwv():
    with patched("post", {"count": 1, "results": []}) as post:
        seo.batch_audit(["https://a.com"], "k")
        assert post.call_args.kwargs["json"] == {"urls": ["https://a.com"]}
        seo.batch_audit(["https://a.com"], "k", cwv=True)
        assert post.call_args.kwargs["json"] == {"urls": ["https://a.com"], "cwv": True}
    assert post.call_args.args[0] == B + "/audit/batch"

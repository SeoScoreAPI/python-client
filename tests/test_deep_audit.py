"""Deep Site Audit client tests. No network: requests.get/post are patched."""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import seoscoreapi as seo  # noqa: E402


class FakeResponse:
    def __init__(self, payload=None, status=200, headers=None):
        self._payload = payload or {}
        self.status_code = status
        self.headers = headers or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise seo.requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(seo.time, "sleep", lambda s: None)


def test_defaults_to_main_host():
    assert seo.DEEP_AUDIT_URL == "https://seoscoreapi.com"
    assert seo.__version__ == "1.5.0"


def test_site_audit_posts_to_main_host():
    with mock.patch.object(seo.requests, "post", return_value=FakeResponse({"job_id": "abc", "status": "queued"})) as post:
        job = seo.site_audit("https://example.com", "k", business_type="saas")
    assert job["job_id"] == "abc"
    args, kwargs = post.call_args
    assert args[0] == "https://seoscoreapi.com/site-audit"
    assert kwargs["json"] == {"url": "https://example.com", "business_type": "saas"}
    assert kwargs["headers"]["X-API-Key"] == "k"


def test_get_site_audit_url():
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({"status": "running"})) as get:
        seo.get_site_audit("abc", "k")
    assert get.call_args[0][0] == "https://seoscoreapi.com/site-audit/abc"


def test_base_url_override_per_call():
    with mock.patch.object(seo.requests, "post", return_value=FakeResponse({"job_id": "x"})) as post:
        seo.site_audit("https://example.com", "k", base_url="http://localhost:9000/")
    assert post.call_args[0][0] == "http://localhost:9000/site-audit"
    assert "base_url" not in post.call_args[1]["json"]


def test_module_override(monkeypatch):
    monkeypatch.setattr(seo, "DEEP_AUDIT_URL", "https://staging.example")
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({})) as get:
        seo.get_site_audit("abc", "k")
    assert get.call_args[0][0] == "https://staging.example/site-audit/abc"


def test_usage_main_host_path():
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({"tier": "pro"})) as get:
        assert seo.deep_audit_usage("k") == {"tier": "pro"}
    assert get.call_args[0][0] == "https://seoscoreapi.com/deep-audit/usage"


def test_usage_legacy_engine_path_and_alias():
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({})) as get:
        seo.engine_usage("k", base_url=seo.ENGINE_URL)
    assert get.call_args[0][0] == "https://engine.seoscoreapi.com/usage"


def test_wait_for_site_audit_completes():
    seq = [
        FakeResponse({"status": "queued", "eta_seconds": 30}),
        FakeResponse({"status": "running", "progress": 50}),
        FakeResponse({"status": "completed", "result": {"scores": {"lai_score": 3.2}}}),
    ]
    seen = []
    with mock.patch.object(seo.requests, "get", side_effect=seq):
        result = seo.wait_for_site_audit("abc", "k", on_progress=lambda s: seen.append(s["status"]))
    assert result == {"scores": {"lai_score": 3.2}}
    assert seen == ["queued", "running", "completed"]


def test_wait_for_site_audit_failed():
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({"status": "failed", "error": "boom"})):
        with pytest.raises(RuntimeError, match="boom"):
            seo.wait_for_site_audit("abc", "k")


def test_wait_for_site_audit_timeout():
    with mock.patch.object(seo.requests, "get", return_value=FakeResponse({"status": "running"})):
        with pytest.raises(TimeoutError):
            seo.wait_for_site_audit("abc", "k", timeout=0)


def test_deep_audit_retries_backpressure_then_polls():
    posts = [
        FakeResponse(status=429, headers={"Retry-After": "1"}),
        FakeResponse({"job_id": "abc", "status": "queued"}),
    ]
    with mock.patch.object(seo.requests, "post", side_effect=posts) as post, \
         mock.patch.object(seo.requests, "get", return_value=FakeResponse({"status": "completed", "result": {"ok": 1}})) as get:
        assert seo.deep_audit("https://example.com", "k") == {"ok": 1}
    assert post.call_count == 2
    assert get.call_args[0][0] == "https://seoscoreapi.com/site-audit/abc"

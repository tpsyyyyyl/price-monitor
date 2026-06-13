import os
import tempfile

# Must be set before any backend import.
os.environ.setdefault("DATABASE_PATH", os.path.join(tempfile.mkdtemp(), "test_extract.db"))
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
os.environ.pop("TELEGRAM_CHAT_ID", None)

import pytest
from fastapi.testclient import TestClient

from backend import ai, extract
from backend.main import app
from backend.scraper.errors import FetchError

client = TestClient(app)

FIXTURE_HTML = """<html>
<head><title>Test Page</title></head>
<body>
<h1>Items list</h1>
<p>Item A - price 10</p>
<p>Item B - price 20</p>
</body>
</html>"""


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def token():
    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    return r.json()["token"]


def _make_fake_client(results, summary="two items"):
    """Returns a fake Groq client whose completions.create returns given results."""
    import json

    class FakeMessage:
        content = json.dumps({"results": results, "summary": summary})

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    class FakeCompletions:
        def create(self, **kwargs):
            return FakeResponse()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    return FakeClient()


# --- tests ---

def test_extract_returns_results(token, monkeypatch):
    fake_results = [{"title": "A"}, {"title": "B"}]
    monkeypatch.setattr(extract, "fetch_html", lambda url: FIXTURE_HTML)
    monkeypatch.setattr(ai, "_get_client", lambda: _make_fake_client(fake_results))

    r = client.post(
        "/api/extract",
        json={"url": "https://example.com/page", "query": "list items"},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 2
    assert data["source"] == "ai"
    assert data["results"] == fake_results


def test_extract_empty_results(token, monkeypatch):
    monkeypatch.setattr(extract, "fetch_html", lambda url: FIXTURE_HTML)
    monkeypatch.setattr(ai, "_get_client", lambda: _make_fake_client([], summary="nothing found"))

    r = client.post(
        "/api/extract",
        json={"url": "https://example.com/page", "query": "nothing here"},
        headers=auth_header(token),
    )
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 0
    assert data["results"] == []


def test_extract_fetch_error_returns_502(token, monkeypatch):
    def boom(url):
        raise FetchError("network down")

    monkeypatch.setattr(extract, "fetch_html", boom)

    r = client.post(
        "/api/extract",
        json={"url": "https://unreachable.example.com/", "query": "anything"},
        headers=auth_header(token),
    )
    assert r.status_code == 502


def test_extract_requires_auth():
    r = client.post(
        "/api/extract",
        json={"url": "https://example.com/", "query": "test"},
    )
    assert r.status_code == 401

import os
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
# гарантуємо, що Telegram вимкнено в тестах (без мережі)
os.environ.pop("TELEGRAM_BOT_TOKEN", None)
os.environ.pop("TELEGRAM_CHAT_ID", None)

import pytest
from fastapi.testclient import TestClient

from backend import ai, notify
from backend.main import app
from backend.scraper import runner
from backend.scraper.errors import UnsupportedSiteError
from backend.scraper.service import ScrapeResult

client = TestClient(app)

BOOKS_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def ensure_product(token: str, url: str = BOOKS_URL) -> int:
    """Створює товар (або повертає id вже існуючого — workspace спільний)."""
    r = client.post("/api/products", json={"url": url}, headers=auth(token))
    if r.status_code == 201:
        return r.json()["id"]
    assert r.status_code == 409
    items = client.get("/api/products", headers=auth(token)).json()
    return next(p["id"] for p in items if p["url"] == url)


@pytest.fixture
def token():
    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def mock_scrape(monkeypatch):
    """scrape_product повертає фіксований результат — без мережі."""
    def fake(url: str) -> ScrapeResult:
        if "example.com" in url:
            raise UnsupportedSiteError("no adapter")
        return ScrapeResult(name="A Light in the Attic", price=51.77, currency="GBP", site="books_toscrape")

    # патчимо в обох місцях, де його імпортовано
    monkeypatch.setattr("backend.routes_products.scrape_product", fake)
    monkeypatch.setattr("backend.scraper.runner.scrape_product", fake)
    return fake


# --- auth ---

def test_demo_login_returns_token():
    r = client.post("/api/auth/demo")
    assert r.status_code == 200
    assert "token" in r.json()


def test_endpoints_require_auth():
    assert client.get("/api/products").status_code == 401
    assert client.post("/api/products", json={"url": BOOKS_URL}).status_code == 401


# --- products CRUD ---

def test_add_product_and_list(token, mock_scrape):
    r = client.post("/api/products", json={"url": BOOKS_URL}, headers=auth(token))
    assert r.status_code == 201
    assert r.json()["current_price"] == 51.77

    r = client.get("/api/products", headers=auth(token))
    assert r.status_code == 200
    items = r.json()
    assert any(p["url"] == BOOKS_URL and p["current_price"] == 51.77 for p in items)


def test_duplicate_url_conflict(token, mock_scrape):
    client.post("/api/products", json={"url": BOOKS_URL}, headers=auth(token))
    r = client.post("/api/products", json={"url": BOOKS_URL}, headers=auth(token))
    assert r.status_code == 409


def test_unsupported_site(token, mock_scrape):
    r = client.post(
        "/api/products", json={"url": "https://example.com/x"}, headers=auth(token)
    )
    assert r.status_code == 400


def test_history_and_pct_change(token, mock_scrape, monkeypatch):
    pid = ensure_product(token)

    # друга точка з іншою ціною через run_all (мокнутий скрейп повертає 51.77,
    # тож рухаємо ціну детерміновано через jitter з мокнутим random)
    monkeypatch.setattr(runner.random, "choice", lambda seq: 1)
    monkeypatch.setattr(runner.random, "uniform", lambda a, b: 0.06)  # +6% > 5% поріг

    before = len(client.get(f"/api/products/{pid}/history", headers=auth(token)).json())
    r = client.post("/api/scrape?jitter=true", headers=auth(token))
    summary = r.json()
    assert summary["scraped"] >= 1

    points = client.get(f"/api/products/{pid}/history", headers=auth(token)).json()
    assert len(points) == before + 1
    assert len(points) >= 2

    r = client.get("/api/products", headers=auth(token))
    prod = next(p for p in r.json() if p["id"] == pid)
    assert prod["pct_change"] is not None


def test_delete_product(token, mock_scrape):
    pid = ensure_product(token, url="https://books.toscrape.com/catalogue/delete-me_1/index.html")
    r = client.delete(f"/api/products/{pid}", headers=auth(token))
    assert r.status_code == 204
    r = client.get(f"/api/products/{pid}/history", headers=auth(token))
    assert r.status_code == 404


def test_csv_export(token, mock_scrape):
    pid = ensure_product(token)
    r = client.get(f"/api/products/{pid}/export.csv", headers=auth(token))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    first_line = r.text.splitlines()[0]
    assert first_line == "scraped_at,price,currency"


# --- AI insight fallback ---

def test_insight_heuristic_fallback(token, mock_scrape, monkeypatch):
    pid = ensure_product(token)

    def boom(*a, **k):
        raise RuntimeError("no AI")

    # _get_client кидає → price_insight падає на евристику
    monkeypatch.setattr(ai, "_get_client", boom)

    r = client.get(f"/api/products/{pid}/insight", headers=auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["source"] == "heuristic"
    assert data["trend"] in ("up", "down", "stable")
    assert data["recommendation"]
    assert data["summary"]


# --- alert path triggers notify ---

def test_large_change_triggers_notify(token, mock_scrape, monkeypatch):
    # свіжий товар з однією точкою (51.77), щоб наступний скрейп дав явну зміну
    pid = ensure_product(token, url="https://books.toscrape.com/catalogue/alert-me_1/index.html")

    calls = []
    monkeypatch.setattr(notify, "send_telegram", lambda text: calls.append(text) or True)

    # перший скрейп без jitter фіксує базову ціну 51.77 для всіх товарів,
    # тож наступний +6% jitter дасть зміну > 5% поріг
    client.post("/api/scrape?jitter=false", headers=auth(token))

    monkeypatch.setattr(runner.random, "choice", lambda seq: 1)
    monkeypatch.setattr(runner.random, "uniform", lambda a, b: 0.06)
    r = client.post("/api/scrape?jitter=true", headers=auth(token))
    assert r.json()["alerts"] >= 1
    assert len(calls) >= 1
    assert any("alert-me" in c or "Light" in c for c in calls)

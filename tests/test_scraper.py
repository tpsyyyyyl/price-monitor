import os

import pytest

from backend.scraper.adapters import detect_adapter, parse_price
from backend.scraper.errors import UnsupportedSiteError
from backend.scraper.service import parse_product

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name: str) -> str:
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


# --- parse_price unit cases ---

def test_parse_price_pounds():
    assert parse_price("£51.77") == 51.77


def test_parse_price_thousands_separator():
    assert parse_price("$1,099.00") == 1099.0


def test_parse_price_european_decimal_comma():
    # "€15,99" — кома як десятковий роздільник → 15.99
    assert parse_price("€15,99") == 15.99


def test_parse_price_invalid_raises():
    from backend.scraper.errors import ParseError

    with pytest.raises(ParseError):
        parse_price("free")


# --- detect_adapter ---

def test_detect_adapter_books():
    adapter = detect_adapter(
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    )
    assert adapter.key == "books_toscrape"


def test_detect_adapter_scrapeme():
    adapter = detect_adapter("https://scrapeme.live/product/bulbasaur/")
    assert adapter.key == "scrapeme"


def test_detect_adapter_unknown_host():
    with pytest.raises(UnsupportedSiteError):
        detect_adapter("https://example.com/product/123")


# --- offline parsing of real fixtures ---

def test_parse_books_fixture():
    adapter = detect_adapter("https://books.toscrape.com/catalogue/x/index.html")
    result = parse_product(_load("books_toscrape.html"), adapter)
    assert result.name == "A Light in the Attic"
    assert result.price == 51.77
    assert result.currency == "GBP"
    assert result.site == "books_toscrape"


def test_parse_scrapeme_fixture():
    adapter = detect_adapter("https://scrapeme.live/product/bulbasaur/")
    result = parse_product(_load("scrapeme.html"), adapter)
    assert result.name == "Bulbasaur"
    assert result.price == 63.0
    assert result.currency == "GBP"
    assert result.site == "scrapeme"

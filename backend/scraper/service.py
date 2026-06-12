"""Високорівневий скрейпінг одного товару: fetch + parse через адаптер."""

from dataclasses import dataclass

from bs4 import BeautifulSoup

from .adapters import SiteAdapter, detect_adapter, parse_price
from .errors import ParseError
from .fetch import fetch_html


@dataclass
class ScrapeResult:
    name: str
    price: float
    currency: str
    site: str


def parse_product(html: str, adapter: SiteAdapter) -> ScrapeResult:
    """Розбирає HTML товару через заданий адаптер.

    Кидає ParseError, якщо селектори назви чи ціни нічого не знайшли —
    зазвичай це означає, що структура сторінки змінилась.
    """
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one(adapter.title_selector)
    price_el = soup.select_one(adapter.price_selector)
    if title_el is None or price_el is None:
        raise ParseError(
            f"Не знайдено назву чи ціну на сторінці ({adapter.key}) — "
            "можливо, змінилась структура сайту."
        )

    name = title_el.get_text(strip=True)
    if not name:
        raise ParseError(f"Порожня назва товару ({adapter.key}).")

    price = parse_price(price_el.get_text())
    return ScrapeResult(
        name=name, price=price, currency=adapter.currency, site=adapter.key
    )


def scrape_product(url: str) -> ScrapeResult:
    """Завантажує сторінку товару й повертає назву, ціну, валюту та сайт."""
    adapter = detect_adapter(url)
    html = fetch_html(url)
    return parse_product(html, adapter)

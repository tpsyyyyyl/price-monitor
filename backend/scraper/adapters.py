"""Реєстр адаптерів магазинів: кожен знає свої CSS-селектори та валюту.

Додати новий магазин = додати один SiteAdapter у ADAPTERS.
"""

from dataclasses import dataclass
from urllib.parse import urlparse

from .errors import ParseError, UnsupportedSiteError

# Символи валют, які треба прибрати перед парсингом числа.
_CURRENCY_SYMBOLS = "£$€"


def parse_price(text: str) -> float:
    """Перетворює рядок ціни на float.

    Прибирає символи валют, пробіли та роздільники тисяч. Правило для коми:
    - якщо є і кома, і крапка ("$1,099.00") — кома це роздільник тисяч → прибираємо;
    - якщо є тільки кома ("€15,99") — це європейський десятковий роздільник → крапка.

    Кидає ParseError, якщо в тексті немає числа.
    """
    cleaned = text.strip()
    for sym in _CURRENCY_SYMBOLS:
        cleaned = cleaned.replace(sym, "")
    cleaned = cleaned.replace("\xa0", "").replace(" ", "")

    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError as e:
        raise ParseError(f"Не вдалося розпарсити ціну з тексту: {text!r}") from e


@dataclass(frozen=True)
class SiteAdapter:
    key: str
    host_fragment: str
    title_selector: str
    price_selector: str
    currency: str

    def match(self, host: str) -> bool:
        return self.host_fragment in host


ADAPTERS: list[SiteAdapter] = [
    SiteAdapter(
        key="books_toscrape",
        host_fragment="books.toscrape.com",
        title_selector="div.product_main h1",
        price_selector="p.price_color",
        currency="GBP",
    ),
    SiteAdapter(
        key="scrapeme",
        host_fragment="scrapeme.live",
        title_selector="h1.product_title",
        price_selector="p.price .woocommerce-Price-amount",
        currency="GBP",
    ),
]


def detect_adapter(url: str) -> SiteAdapter:
    """Підбирає адаптер за хостом URL. Кидає UnsupportedSiteError, якщо немає."""
    host = (urlparse(url).hostname or "").lower()
    for adapter in ADAPTERS:
        if adapter.match(host):
            return adapter
    raise UnsupportedSiteError(f"Немає адаптера для сайту: {host or url!r}")

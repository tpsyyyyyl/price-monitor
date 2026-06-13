"""Universal AI extractor: fetch any URL and extract items matching a query."""

import json
import re

from bs4 import BeautifulSoup

from . import ai
from .scraper.errors import FetchError  # noqa: F401 — re-exported for callers
from .scraper.fetch import fetch_html

_MAX_TEXT = 40000
_PRICE_KEYS = {"price", "lowprice", "highprice", "pricecurrency"}


def _coerce_price(raw) -> float:
    """Turn an AI-returned price into a float, robust to any locale/currency.

    Handles plain numbers, currency words/symbols (₴, грн, UAH, £, $, …), and
    space/comma/dot thousand & decimal separators ("66 699 ₴", "1,099.00",
    "15,99 €"). Raises ValueError if no number can be recovered.
    """
    if isinstance(raw, (int, float)):
        return float(raw)
    # Keep only digits and separators — drops letters, currency symbols, spaces.
    s = re.sub(r"[^\d.,]", "", str(raw))
    if "," in s and "." in s:
        s = s.replace(",", "")  # comma = thousands separator
    elif "," in s:
        # Comma is decimal only when 1–2 digits trail it ("15,99"); else thousands.
        s = s.replace(",", ".") if re.search(r",\d{1,2}$", s) else s.replace(",", "")
    try:
        return float(s)
    except ValueError as e:
        raise ValueError(f"Could not parse a price from {raw!r}") from e


def _walk_json(obj, found):
    """Recursively collect price-related key/values from parsed JSON-LD."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in _PRICE_KEYS and isinstance(value, (str, int, float)):
                found.append(f"{key}: {value}")
            else:
                _walk_json(value, found)
    elif isinstance(obj, list):
        for item in obj:
            _walk_json(item, found)


def _structured_price_signals(soup: BeautifulSoup) -> str:
    """Extract machine-readable price hints (JSON-LD + meta) before stripping.

    E-commerce pages bury the price deep in heavy markup but almost always also
    expose it as structured data — which we'd otherwise discard with <script>.
    """
    found: list[str] = []

    # JSON-LD structured data (lives inside <script type="application/ld+json">)
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or tag.get_text()
        if not raw:
            continue
        try:
            _walk_json(json.loads(raw), found)
        except (ValueError, TypeError):
            continue

    # Open Graph / product / microdata meta tags
    meta_wanted = {
        "og:price:amount", "product:price:amount", "og:price:currency",
        "product:price:currency", "price", "pricecurrency",
    }
    for tag in soup.find_all("meta"):
        key = tag.get("property") or tag.get("itemprop") or tag.get("name")
        if key and key.lower() in meta_wanted and tag.get("content"):
            found.append(f"{key}: {tag['content']}")

    # Microdata elements with itemprop="price"
    for tag in soup.find_all(attrs={"itemprop": "price"}):
        val = tag.get("content") or tag.get_text(strip=True)
        if val:
            found.append(f"itemprop price: {val}")

    if not found:
        return ""
    seen = list(dict.fromkeys(found))  # dedupe, preserve order
    return "[STRUCTURED DATA]\n" + "\n".join(seen[:20]) + "\n\n"


def _html_to_text(html: str) -> str:
    """Converts raw HTML to clean plain text, truncated to _MAX_TEXT chars.

    Prepends structured price signals so they survive truncation on heavy pages.
    """
    soup = BeautifulSoup(html, "html.parser")

    signals = _structured_price_signals(soup)  # read scripts/meta BEFORE stripping

    for tag in soup.find_all(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title_tag = soup.find("title")
    title_prefix = f"{title_tag.get_text(strip=True)}\n\n" if title_tag else ""

    text = title_prefix + signals + soup.get_text(separator="\n")
    # Collapse runs of blank lines into a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text[:_MAX_TEXT]


def extract_from_url(url: str, query: str) -> dict:
    """Fetch url, clean its text, run AI extraction, return enriched result dict.

    Raises FetchError if the page cannot be downloaded (caller handles it).
    """
    html = fetch_html(url)
    text = _html_to_text(html)
    result = ai.extract_items(text, query)
    result["count"] = len(result.get("results", []))
    return result


def ai_scrape(url: str, target_name: str | None = None) -> dict:
    """Скрейп будь-якого сайту через AI: fetch → text → витяг назви й ціни.

    Пробрасує FetchError, якщо сторінку не завантажити. Кидає ValueError, якщо
    ціну не вдалося визначити чи перетворити на число.

    Повертає {"name": str, "price": float, "currency": str, "site": "ai"}.
    """
    html = fetch_html(url)
    text = _html_to_text(html)
    data = ai.extract_product_price(text, target_name)

    price = _coerce_price(data["price"])

    return {
        "name": data["name"],
        "price": price,
        "currency": data["currency"],
        "site": "ai",
    }

"""Universal AI extractor: fetch any URL and extract items matching a query."""

import re

from bs4 import BeautifulSoup

from . import ai
from .scraper.errors import FetchError  # noqa: F401 — re-exported for callers
from .scraper.fetch import fetch_html

_MAX_TEXT = 18000


def _html_to_text(html: str) -> str:
    """Converts raw HTML to clean plain text, truncated to _MAX_TEXT chars."""
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    title_tag = soup.find("title")
    title_prefix = f"{title_tag.get_text(strip=True)}\n\n" if title_tag else ""

    text = title_prefix + soup.get_text(separator="\n")
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

"""Завантаження HTML сторінок товарів через httpx з браузерним UA та одним ретраєм."""

import time

import httpx

from .errors import FetchError

# Браузероподібний User-Agent — деякі магазини блокують "голі" клієнти.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT = 15.0


def fetch_html(url: str) -> str:
    """Завантажує сторінку й повертає її HTML.

    Робить один повторний запит на тимчасову помилку (мережа/HTTP), щоб не
    падати через випадковий збій. Кидає FetchError зі зрозумілим повідомленням,
    якщо обидві спроби не вдалися.
    """
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            resp = httpx.get(
                url, headers=HEADERS, timeout=TIMEOUT, follow_redirects=True
            )
            resp.raise_for_status()
            return resp.text
        except httpx.HTTPError as e:
            last_error = e
            if attempt == 0:
                time.sleep(1.0)  # коротка пауза перед єдиним ретраєм

    raise FetchError(f"Не вдалося завантажити {url}: {last_error}") from last_error

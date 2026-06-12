"""Telegram-сповіщення про зміну ціни.

Якщо TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не задані — сповіщення вимкнені:
повідомлення лише логується, мережевого запиту немає. send_telegram ніколи
не кидає виняток, щоб збій сповіщення не зривав скрейп-батч.
"""

import logging
import os

import httpx

logger = logging.getLogger("price_monitor.notify")

API_URL = "https://api.telegram.org/bot{token}/sendMessage"
TIMEOUT = 10.0


def send_telegram(text: str) -> bool:
    """Надсилає повідомлення в Telegram. Повертає True, якщо відправлено."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        logger.info("[telegram disabled] " + text)
        return False

    try:
        resp = httpx.post(
            API_URL.format(token=token),
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning("Не вдалося надіслати Telegram-сповіщення: %s", e)
        return False


def price_change_message(product, old: float, new: float, pct: float) -> str:
    """Один рядок про зміну ціни: стрілка напрямку, назва, old→new, %, url."""
    arrow = "📉" if new < old else "📈"
    cur = product.currency
    return (
        f"{arrow} *{product.name}*: {old:.2f} → {new:.2f} {cur} "
        f"({pct:+.1f}%)\n{product.url}"
    )

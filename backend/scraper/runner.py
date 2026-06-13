"""Пакетний скрейп усіх активних товарів: фіксує нові ціни й шле сповіщення.

Одна помилка по товару ніколи не валить весь батч — логуємо й продовжуємо.
"""

import logging
import random

from sqlalchemy.orm import Session

from .. import notify
from ..models import PricePoint, Product, utcnow
from .service import scrape_product

logger = logging.getLogger("price_monitor.runner")

# Поріг зміни ціни (у %), за яким шлемо Telegram-сповіщення.
ALERT_THRESHOLD_PCT = 5.0


def _jitter_price(price: float) -> float:
    """Демо-режим: збурює ціну на ±2–8%, щоб історія «оживала» без реального скрейпу."""
    factor = 1 + random.choice([-1, 1]) * random.uniform(0.02, 0.08)
    return round(price * factor, 2)


def run_all(db: Session, jitter: bool = False) -> dict:
    """Скрейпить кожен активний товар, додає PricePoint, шле алерти.

    Повертає підсумок {scraped, failed, alerts}.
    """
    products = db.query(Product).filter(Product.is_active.is_(True)).all()
    scraped = 0
    failed = 0
    alerts = 0

    from .. import extract  # локальний імпорт, щоб уникнути циклічного

    for product in products:
        try:
            if product.site == "ai":
                result = extract.ai_scrape(product.url, target_name=product.name)
                new_price = result["price"]
            else:
                new_price = scrape_product(product.url).price
        except Exception as e:
            failed += 1
            logger.warning("Скрейп не вдався для %s: %s", product.url, e)
            continue

        price = _jitter_price(new_price) if jitter else new_price

        previous = product.points[-1].price if product.points else None

        db.add(PricePoint(product_id=product.id, price=price))
        product.last_checked_at = utcnow()
        db.commit()
        scraped += 1

        if previous:
            pct = (price - previous) / previous * 100
            if abs(pct) > ALERT_THRESHOLD_PCT:
                alerts += 1
                notify.send_telegram(
                    notify.price_change_message(product, previous, price, pct)
                )

    return {"scraped": scraped, "failed": failed, "alerts": alerts}

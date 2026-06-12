"""Створює демо-користувача й ~5 товарів з історією цін. Run: python -m backend.seed_demo

Без мережі: назви/сайти/валюти захардкоджені, історія (21 точка) генерується
м'яким випадковим блуканням ±3% з одним більшим спадом/стрибком, щоб графіки
виглядали живими. Повторний запуск нічого не дублює (ідемпотентно).
"""

import random
from datetime import timedelta

from .auth import DEMO_EMAIL, DEMO_PASSWORD, hash_password
from .database import Base, SessionLocal, engine
from .models import PricePoint, Product, User, utcnow

# Реальні URL (books.toscrape.com — каталог; scrapeme.live/shop), але дані
# беремо захардкоджені, без мережевого запиту під час сидінгу.
SAMPLES = [
    {
        "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "name": "A Light in the Attic",
        "site": "books_toscrape",
        "currency": "GBP",
        "base_price": 51.77,
    },
    {
        "url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
        "name": "Tipping the Velvet",
        "site": "books_toscrape",
        "currency": "GBP",
        "base_price": 53.74,
    },
    {
        "url": "https://books.toscrape.com/catalogue/soumission_998/index.html",
        "name": "Soumission",
        "site": "books_toscrape",
        "currency": "GBP",
        "base_price": 50.10,
    },
    {
        "url": "https://scrapeme.live/shop/Bulbasaur/",
        "name": "Bulbasaur",
        "site": "scrapeme",
        "currency": "GBP",
        "base_price": 63.00,
    },
    {
        "url": "https://scrapeme.live/shop/Charmander/",
        "name": "Charmander",
        "site": "scrapeme",
        "currency": "GBP",
        "base_price": 165.00,
    },
]

POINTS = 21


def _price_history(base_price: float, rng: random.Random) -> list[float]:
    """21 денна ціна: випадкове блукання ±3% + один більший спад/стрибок."""
    spike_day = rng.randint(5, POINTS - 4)
    spike_factor = rng.choice([0.85, 0.88, 1.12, 1.15])

    prices = []
    price = base_price
    for day in range(POINTS):
        step = 1 + rng.uniform(-0.03, 0.03)
        price *= step
        value = price * spike_factor if day == spike_day else price
        prices.append(round(value, 2))
    return prices


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()

        created = 0
        now = utcnow()
        for s in SAMPLES:
            if db.query(Product).filter(Product.url == s["url"]).first():
                continue

            rng = random.Random(s["url"])  # детерміновано на товар
            history = _price_history(s["base_price"], rng)

            product = Product(
                url=s["url"],
                name=s["name"],
                site=s["site"],
                currency=s["currency"],
                last_checked_at=now,
            )
            db.add(product)
            db.flush()

            for i, price in enumerate(history):
                scraped_at = now - timedelta(days=POINTS - 1 - i)
                db.add(PricePoint(product_id=product.id, price=price, scraped_at=scraped_at))
            created += 1

        db.commit()
        if created:
            print(f"Demo seeded: {DEMO_EMAIL} with {created} new products ({POINTS} points each).")
        else:
            print("Demo data already present, nothing to do.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

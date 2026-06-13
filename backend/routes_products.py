import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from urllib.parse import urlparse

from . import ai, extract
from .auth import get_current_user
from .database import get_db
from .models import PricePoint, Product, User, utcnow
from .scraper import adapters
from .scraper.errors import FetchError, ParseError, UnsupportedSiteError
from .scraper.runner import run_all
from .scraper.service import scrape_product

router = APIRouter(prefix="/api", tags=["products"])


class CreateProductRequest(BaseModel):
    url: str
    name: str | None = None
    price: float | str | None = None
    currency: str | None = None


def _pct_change(current: float, previous: float | None) -> float | None:
    if previous is None or previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def _summary(product: Product) -> dict:
    points = product.points
    current = points[-1].price if points else None
    previous = points[-2].price if len(points) >= 2 else None
    return {
        "id": product.id,
        "name": product.name,
        "url": product.url,
        "site": product.site,
        "currency": product.currency,
        "is_active": product.is_active,
        "last_checked_at": product.last_checked_at,
        "current_price": current,
        "previous_price": previous,
        "pct_change": _pct_change(current, previous) if current is not None else None,
    }


def _get_product(product_id: int, db: Session) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/products", status_code=201)
def create_product(
    req: CreateProductRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    url = req.url.strip()
    if db.query(Product).filter(Product.url == url).first():
        raise HTTPException(status_code=409, detail="This product is already tracked")

    if req.price is not None:
        # Фронтенд уже знає назву й ціну ("Track this result") — без мережі.
        if isinstance(req.price, str):
            try:
                price = adapters.parse_price(req.price)
            except ParseError as e:
                raise HTTPException(status_code=422, detail=str(e))
        else:
            price = float(req.price)
        name = req.name or (urlparse(url).hostname or url)
        currency = req.currency or "USD"
        site = "ai"
    else:
        try:
            adapters.detect_adapter(url)
            result = scrape_product(url)
            name = result.name
            price = result.price
            currency = result.currency
            site = result.site
        except UnsupportedSiteError:
            try:
                result = extract.ai_scrape(url)
            except FetchError as e:
                raise HTTPException(status_code=502, detail=str(e))
            except ValueError:
                raise HTTPException(
                    status_code=422,
                    detail="Не вдалося визначити ціну на цій сторінці",
                )
            name = result["name"]
            price = result["price"]
            currency = result["currency"]
            site = result["site"]
        except FetchError as e:
            raise HTTPException(status_code=502, detail=str(e))
        except ParseError as e:
            raise HTTPException(status_code=422, detail=str(e))

    product = Product(
        url=url,
        name=name,
        site=site,
        currency=currency,
        last_checked_at=utcnow(),
    )
    db.add(product)
    db.flush()
    db.add(PricePoint(product_id=product.id, price=price))
    db.commit()
    return _summary(product)


@router.get("/products")
def list_products(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.created_at.desc()).all()
    return [_summary(p) for p in products]


@router.get("/products/{product_id}/history")
def product_history(
    product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    product = _get_product(product_id, db)
    return [
        {"price": p.price, "scraped_at": p.scraped_at} for p in product.points
    ]


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    product = _get_product(product_id, db)
    db.delete(product)
    db.commit()


@router.get("/products/{product_id}/export.csv")
def export_csv(
    product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    product = _get_product(product_id, db)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["scraped_at", "price", "currency"])
    for p in product.points:
        writer.writerow([p.scraped_at.isoformat(), f"{p.price:.2f}", product.currency])
    buf.seek(0)

    filename = f"product-{product.id}-prices.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/scrape")
def scrape_now(
    jitter: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return run_all(db, jitter=jitter)


@router.get("/products/{product_id}/insight")
def product_insight(
    product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    product = _get_product(product_id, db)
    return ai.price_insight(product, product.points)

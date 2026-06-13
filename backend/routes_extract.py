from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .auth import get_current_user
from .extract import extract_from_url
from .models import User
from .scraper.errors import FetchError

router = APIRouter(prefix="/api", tags=["extract"])


class ExtractRequest(BaseModel):
    url: str
    query: str


@router.post("/extract")
def extract(req: ExtractRequest, user: User = Depends(get_current_user)):
    try:
        return extract_from_url(req.url, req.query)
    except FetchError:
        raise HTTPException(status_code=502, detail="Не вдалося завантажити сторінку")

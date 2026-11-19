from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.db import get_session
from app.modules.search import service
from app.modules.search.schemas import SearchOut

router = APIRouter(prefix="/api/search")


@router.get("/products", response_model=SearchOut)
def search_products(
    session=Depends(get_session),
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price_cents: Optional[int] = Query(None),
    max_price_cents: Optional[int] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    return service.search_products(
        session,
        query=q,
        category=category,
        min_price_cents=min_price_cents,
        max_price_cents=max_price_cents,
        min_rating=min_rating,
        sort=sort,
        page=page,
        page_size=page_size
    )

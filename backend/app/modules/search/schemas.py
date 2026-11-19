from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price_cents: int
    list_price_cents: Optional[int]
    stock: int
    category: str
    image_url: Optional[str]
    brand: Optional[str]
    warranty_months: Optional[int]
    model_number: Optional[str]
    seller_id: int
    average_rating: float
    review_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class SearchOut(BaseModel):
    items: List[ProductOut]
    total: int
    page: int
    page_size: int
    corrected_query: Optional[str]

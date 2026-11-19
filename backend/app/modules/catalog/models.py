from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core import clock
from app.core.db import UTCDateTime


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    price_cents: int = Field(gt=0)
    list_price_cents: Optional[int] = Field(default=None, gt=0)
    stock: int = Field(default=0, ge=0)
    category: str = Field(max_length=255, index=True)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    brand: Optional[str] = Field(default=None, max_length=255)
    warranty_months: Optional[int] = Field(default=None, ge=0)
    model_number: Optional[str] = Field(default=None, max_length=255)
    seller_id: int = Field(index=True)
    average_rating: float = Field(default=0.0)
    review_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=clock.utcnow, sa_type=UTCDateTime)

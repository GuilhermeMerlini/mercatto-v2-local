from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ProductIn(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    price_cents: int = Field(..., gt=0)
    list_price_cents: Optional[int] = Field(default=None, gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., max_length=255)
    image_url: Optional[str] = Field(default=None, max_length=1000)
    brand: Optional[str] = Field(default=None, max_length=255)
    warranty_months: Optional[int] = Field(default=None, ge=0)
    model_number: Optional[str] = Field(default=None, max_length=255)

    @validator("name", "category")
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("cannot be empty or only whitespace")
        return v.strip()


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

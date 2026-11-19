
from pydantic import BaseModel, Field


class CartItemIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)


class CartItemUpdate(BaseModel):
    quantity: int = Field(gt=0)

from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class CartItem(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user.id")
    product_id: int = Field(foreign_key="catalog.product.id")
    quantity: int
    created

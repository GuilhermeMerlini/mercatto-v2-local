from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

from app.core.clock import utcnow
from app.core.db import UTCDateTime


class CartItem(SQLModel, table=True):
    __tablename__ = "cart_item"
    __table_args__ = (UniqueConstraint("user_id", "product_id"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    product_id: int = Field(index=True)
    quantity: int = Field(gt=0)
    saved_for_later: bool = Field(default=False)
    added_at: datetime = Field(default_factory=utcnow, sa_type=UTCDateTime)
    updated_at: datetime = Field(default_factory=utcnow, sa_type=UTCDateTime)

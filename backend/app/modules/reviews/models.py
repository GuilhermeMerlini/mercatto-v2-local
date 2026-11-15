from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class Review(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user.id")
    product_id: int = Field(foreign_key="catalog.product.id")
    rating: int = Field(default=0, ge=0, le=5)
    comment: str
    created_at: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    model_config = ConfigDict(arbitrary_types_allowed=True)

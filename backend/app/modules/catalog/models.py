from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    price_cents: int
    stock: int
    created_at: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    model_config = ConfigDict(arbitrary_types_allowed=True)

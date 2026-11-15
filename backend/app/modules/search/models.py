from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class SearchIndex(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="catalog.product.id")
    query: str = Field(index=True)
    created_at: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    model_config = ConfigDict(arbitrary_types_allowed=True)

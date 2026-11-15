from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class Payment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="orders.order.id")
    amount_cents: int
    status: str = Field(default="PENDING")
    processed_at: UTCDateTime = Field(default=None)
    model_config = ConfigDict(arbitrary_types_allowed=True)

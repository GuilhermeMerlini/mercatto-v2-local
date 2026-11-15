from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user.id")
    total_cents: int
    status: str = Field(default="PENDING")
    created_at: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    model_config = ConfigDict(arbitrary_types_allowed=True)

from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class Seller(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.user.id")
    store_name: str = Field(unique=True, index=True)
    created_at: UTC

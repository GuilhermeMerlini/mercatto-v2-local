from sqlmodel import SQLModel, Field
from app.core.types import UTCDateTime
from pydantic import ConfigDict


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: str = Field(default="BUYER")
    created_at: UTCDateTime = Field(default_factory=lambda: UTCDateTime())
    model_config = ConfigDict(arbitrary_types_allowed=True)

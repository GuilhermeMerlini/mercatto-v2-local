from datetime import datetime
from enum import Enum

from sqlmodel import Column, Field, SQLModel

from app.core.clock import utcnow
from app.core.db import UTCDateTime


class UserRole(str, Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: int = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    role: UserRole = Field(default=UserRole.BUYER)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_column=Column(UTCDateTime, nullable=False)
    )

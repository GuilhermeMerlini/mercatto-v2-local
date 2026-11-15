from collections.abc import Iterator
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator
from sqlmodel import Session, SQLModel, create_engine

from app.core import config
from app.core.types import UTCDateTime


engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)


def init_db() -> None:
    from app.modules import registry
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session

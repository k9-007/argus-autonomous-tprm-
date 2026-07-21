"""Database engine + session management (SQLAlchemy 2.0).

Defaults to SQLite for zero-config local runs; set DATABASE_URL to a Postgres
DSN for production multi-tenant deployments.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from .config import settings

_connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False: background crew thread shares the engine.
    # timeout: tolerate brief write locks under concurrent requests + crew.
    _connect_args = {"check_same_thread": False, "timeout": 30}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models  # noqa: F401  (register mappers)

    Base.metadata.create_all(bind=engine)

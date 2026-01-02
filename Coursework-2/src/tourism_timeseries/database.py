"""Database helpers for tourism time-series analysis."""

from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine as _create_engine


def create_engine(url: str = "sqlite:///./tourism.db", echo: bool = False):
    """Create a SQLModel-compatible engine."""
    return _create_engine(url, echo=echo)


def init_db(engine) -> None:
    """Create tables for all SQLModel models."""
    SQLModel.metadata.create_all(engine)


@contextmanager
def create_session(engine) -> Iterator[Session]:
    """Yield a managed session for the provided engine."""
    with Session(engine) as session:
        yield session

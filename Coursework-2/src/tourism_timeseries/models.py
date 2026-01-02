"""SQLModel ORM models for tourism time-series data."""

from datetime import date
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class SeriesMaster(SQLModel, table=True):
    """Represents a time-series grouping such as a market or region."""

    __tablename__ = "series_master"

    series_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    level: Optional[str] = Field(default=None, index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="series_master.series_id")

    observations: list["Observation"] = Relationship(back_populates="series")


class Observation(SQLModel, table=True):
    """Single observation for a market and month."""

    __tablename__ = "observations"

    series_id: int = Field(foreign_key="series_master.series_id", primary_key=True)
    month: date = Field(primary_key=True, index=True)
    value: Optional[float] = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
    )

    series: Optional[SeriesMaster] = Relationship(back_populates="observations")

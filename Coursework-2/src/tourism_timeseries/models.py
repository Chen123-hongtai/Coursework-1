"""SQLModel ORM models for tourism time-series data."""

from datetime import date
from typing import List, Optional, Tuple

from sqlmodel import Session
from sqlmodel import SQLModel, Field, Relationship, Session, select


class SeriesMaster(SQLModel, table=True):
    """Represents a time-series grouping such as a market or region."""

    __tablename__ = "series_master"

    series_id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    level: Optional[str] = Field(default=None, index=True)
    parent_id: Optional[int] = Field(default=None, foreign_key="series_master.series_id")

    observations: list["Observation"] = Relationship(back_populates="series")

    @classmethod
    def get_children(cls, session: Session, parent_id: int) -> List["SeriesMaster"]:
        """
        Return all child series under a given parent (e.g., markets under a region).
        Used to build the Region → Market tree in Market Explorer.
        """
        statement = select(cls).where(cls.parent_id == parent_id).order_by(cls.name)
        return list(session.exec(statement))

    @classmethod
    def get_by_level(cls, session: Session, level: str) -> List["SeriesMaster"]:
        """
        Return all series at a given level (e.g., 'Total', 'Region', or 'Market').
        Used to populate dropdowns and filters in the UI.
        """
        statement = select(cls).where(cls.level == level).order_by(cls.name)
        return list(session.exec(statement))

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

    @classmethod
    def moving_average(
        cls, session: Session, series_id: int, window: int = 12
    ) -> List[Tuple[date, Optional[float]]]:
        """
        Return rolling mean time series for a given series.
        """
        from .analysis import moving_average as _moving_average
        return _moving_average(session, series_id, window=window)
    
    @classmethod
    def yoy_change(cls, session: Session, series_id: int, month: date) -> Optional[float]:
        """
        Compute year-on-year change for a given series and month.
        Implemented as a class-level analysis method to satisfy CW2 requirement
        while keeping analytics logic reusable.
        """
        # Local import avoids circular import at module load time
        from .analysis import yoy_change as _yoy_change
        return _yoy_change(session, series_id, month)
    
    @classmethod
    def missing_rate(
        cls, session: Session, series_id: int, start: date, end: date
    ) -> float:
        """
        Compute missing-value rate for a given series in a date range.
        """
        from .analysis import missing_rate as _missing_rate
        return _missing_rate(session, series_id, start, end)


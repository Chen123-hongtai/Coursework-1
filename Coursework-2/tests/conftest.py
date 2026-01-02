import pytest
from sqlmodel import SQLModel, Session, create_engine
from datetime import date

from tourism_timeseries.models import SeriesMaster, Observation


@pytest.fixture(scope="function")
def engine():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def session(engine):
    with Session(engine) as session:
        # Seed minimal but realistic hierarchy
        root = SeriesMaster(series_id=1, name="Asia", level="region", parent_id=None)
        market = SeriesMaster(series_id=2, name="Japan", level="market", parent_id=1)
        session.add(root)
        session.add(market)

        # Seed monthly observations for time-series tests
        data = [
            Observation(series_id=2, month=date(2023, 1, 1), value=100),
            Observation(series_id=2, month=date(2024, 1, 1), value=120),
            Observation(series_id=2, month=date(2025, 1, 1), value=None),  # missing
        ]

        session.add_all(data)
        session.commit()
        yield session

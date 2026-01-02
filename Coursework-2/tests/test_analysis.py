"""Tests for tourism_timeseries analysis functions."""

from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine

from tourism_timeseries.analysis import missing_rate, moving_average, yoy_change
from tourism_timeseries.models import Observation, SeriesMaster


@pytest.fixture()
def session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def add_observation(session: Session, series_id: int, month: date, value: float | None):
    session.add(Observation(series_id=series_id, month=month, value=value))
    session.commit()


def add_series(session: Session, series_id: int = 1, name: str = "Test Series"):
    session.add(SeriesMaster(series_id=series_id, name=name, level="market"))
    session.commit()


def test_yoy_change_computes_percentage(session: Session):
    """Unit test. GIVEN observations in consecutive years WHEN yoy_change is called THEN the percentage change is returned."""

    add_series(session)
    add_observation(session, 1, date(2023, 1, 1), 100.0)
    add_observation(session, 1, date(2024, 1, 1), 120.0)

    assert yoy_change(session, 1, date(2024, 1, 1)) == 20.0


def test_yoy_change_missing_current_value_returns_none(session: Session):
    """Unit test. GIVEN missing current value WHEN yoy_change is called THEN None is returned."""

    add_series(session)
    add_observation(session, 1, date(2023, 2, 1), 50.0)
    add_observation(session, 1, date(2024, 2, 1), None)

    assert yoy_change(session, 1, date(2024, 2, 1)) is None


def test_yoy_change_missing_previous_value_returns_none(session: Session):
    """Unit test. GIVEN missing previous value WHEN yoy_change is called THEN None is returned."""

    add_series(session)
    add_observation(session, 1, date(2023, 3, 1), None)
    add_observation(session, 1, date(2024, 3, 1), 75.0)

    assert yoy_change(session, 1, date(2024, 3, 1)) is None


def test_yoy_change_previous_zero_returns_none(session: Session):
    """Unit test. GIVEN previous value is zero WHEN yoy_change is called THEN None is returned to avoid division by zero."""

    add_series(session)
    add_observation(session, 1, date(2023, 4, 1), 0.0)
    add_observation(session, 1, date(2024, 4, 1), 10.0)

    assert yoy_change(session, 1, date(2024, 4, 1)) is None


def test_yoy_change_without_previous_observation_returns_none(session: Session):
    """Unit test. GIVEN missing previous year observation WHEN yoy_change is called THEN None is returned."""

    add_series(session)
    add_observation(session, 1, date(2024, 5, 1), 10.0)

    assert yoy_change(session, 1, date(2024, 5, 1)) is None


def test_moving_average_returns_expected_window(session: Session):
    """Unit test. GIVEN sequential observations WHEN moving_average is computed THEN a rolling series is returned."""

    add_series(session)
    for idx, value in enumerate([10.0, 20.0, 30.0], start=1):
        add_observation(session, 1, date(2024, idx, 1), value)

    result = moving_average(session, 1, window=2)
    assert result == [
        (date(2024, 1, 1), None),
        (date(2024, 2, 1), 15.0),
        (date(2024, 3, 1), 25.0),
    ]


def test_moving_average_handles_missing_values(session: Session):
    """Unit test. GIVEN gaps in the series WHEN moving_average is computed THEN missing values are ignored in the rolling mean."""

    add_series(session)
    add_observation(session, 1, date(2024, 1, 1), 10.0)
    add_observation(session, 1, date(2024, 2, 1), None)
    add_observation(session, 1, date(2024, 3, 1), 30.0)

    result = moving_average(session, 1, window=2)
    assert result == [
        (date(2024, 1, 1), None),
        (date(2024, 2, 1), 10.0),
        (date(2024, 3, 1), 30.0),
    ]


def test_moving_average_invalid_window_raises_value_error(session: Session):
    """Unit test. GIVEN non-positive window WHEN moving_average is computed THEN ValueError is raised."""

    add_series(session)
    with pytest.raises(ValueError):
        moving_average(session, 1, window=0)


def test_yoy_change_invalid_month_type_raises(session: Session):
    """Unit test. GIVEN an invalid month argument WHEN yoy_change is called THEN TypeError is raised."""

    add_series(session)
    add_observation(session, 1, date(2024, 1, 1), 5.0)
    with pytest.raises(TypeError):
        yoy_change(session, 1, "2024-01-01")  # type: ignore[arg-type]


def test_missing_rate_computes_fraction(session: Session):
    """Unit test. GIVEN observations with gaps WHEN missing_rate is computed THEN the correct proportion is returned."""

    add_series(session)
    add_observation(session, 1, date(2023, 1, 1), 10.0)
    add_observation(session, 1, date(2023, 2, 1), None)
    add_observation(session, 1, date(2023, 3, 1), 5.0)

    assert missing_rate(session, 1, date(2023, 1, 1), date(2023, 3, 1)) == pytest.approx(1 / 3)


def test_missing_rate_without_observations_raises(session: Session):
    """Unit test. GIVEN no observations in range WHEN missing_rate is computed THEN ValueError is raised."""

    add_series(session)
    with pytest.raises(ValueError):
        missing_rate(session, 1, date(2022, 1, 1), date(2022, 12, 1))


def test_missing_rate_with_invalid_range_raises(session: Session):
    """Unit test. GIVEN start date after end date WHEN missing_rate is computed THEN ValueError is raised."""

    add_series(session)
    with pytest.raises(ValueError):
        missing_rate(session, 1, date(2023, 5, 1), date(2023, 1, 1))


def test_integration_yoy_and_moving_average_with_file_db(tmp_path):
    """Integration test. GIVEN a persisted SQLite database WHEN queries run in a new session THEN analytics return expected results."""

    db_path = tmp_path / "tourism.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(SeriesMaster(series_id=10, name="Integration Series", level="market"))
        session.add_all(
            [
                Observation(series_id=10, month=date(2023, 6, 1), value=50.0),
                Observation(series_id=10, month=date(2024, 6, 1), value=70.0),
                Observation(series_id=10, month=date(2024, 7, 1), value=90.0),
            ]
        )
        session.commit()

    with Session(engine) as session:
        assert yoy_change(session, 10, date(2024, 6, 1)) == 40.0
        ma = moving_average(session, 10, window=2)
        assert ma[-1] == (date(2024, 7, 1), 80.0)

def test_analysis_functions_do_not_modify_database(session):
    """
    GIVEN a database with known observation values (Type: Unit test)
    WHEN analysis functions such as moving_average and yoy_change are executed
    THEN the underlying database records must remain unchanged
    """
    from tourism_timeseries.analysis import moving_average, yoy_change
    from tourism_timeseries.models import Observation
    from datetime import date
    from sqlmodel import select

    # Capture database state BEFORE running analytics
    before = list(session.exec(select(Observation).order_by(Observation.series_id, Observation.month)))

    # Run analysis functions
    _ = moving_average(session, series_id=1, window=12)
    _ = yoy_change(session, series_id=1, month=date(2024, 1, 1))

    # Capture database state AFTER running analytics
    after = list(session.exec(select(Observation).order_by(Observation.series_id, Observation.month)))

    # Compare field-by-field
    assert len(before) == len(after)
    for b, a in zip(before, after):
        assert b.series_id == a.series_id
        assert b.month == a.month
        assert b.value == a.value


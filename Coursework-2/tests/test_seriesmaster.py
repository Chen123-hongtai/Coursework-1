from datetime import date
from sqlmodel import Session

from tourism_timeseries.models import SeriesMaster, Observation


def _add_series(session: Session, series_id: int, name: str, level: str, parent_id: int | None):
    session.add(SeriesMaster(series_id=series_id, name=name, level=level, parent_id=parent_id))
    session.commit()


def _add_obs(session: Session, series_id: int, month: date, value):
    session.add(Observation(series_id=series_id, month=month, value=value))
    session.commit()


# 1) get_children: returns correct children
def test_seriesmaster_get_children_returns_all_children(session: Session):
    """Unit test. GIVEN a region with multiple markets WHEN get_children THEN returns all child markets."""
    _add_series(session, 100, "Asia", "region", None)
    _add_series(session, 101, "Japan", "market", 100)
    _add_series(session, 102, "Korea", "market", 100)

    children = SeriesMaster.get_children(session, parent_id=100)
    child_ids = [c.series_id for c in children]

    assert set(child_ids) == {101, 102}


# 2) get_children: ordered by name
def test_seriesmaster_get_children_is_ordered_by_name(session: Session):
    """Unit test. GIVEN children with names WHEN get_children THEN results are sorted by name."""
    _add_series(session, 200, "Europe", "region", None)
    _add_series(session, 201, "ZetaMarket", "market", 200)
    _add_series(session, 202, "AlphaMarket", "market", 200)

    children = SeriesMaster.get_children(session, parent_id=200)
    names = [c.name for c in children]

    assert names == sorted(names)


# 3) get_children: empty when no children
def test_seriesmaster_get_children_empty_when_no_children(session: Session):
    """Unit test. GIVEN a node with no children WHEN get_children THEN returns empty list."""
    _add_series(session, 300, "Oceania", "region", None)

    children = SeriesMaster.get_children(session, parent_id=300)
    assert children == []


# 4) get_by_level: returns only requested level
def test_seriesmaster_get_by_level_filters_correctly(session: Session):
    """Unit test. GIVEN mixed levels WHEN get_by_level THEN returns only matching series."""
    _add_series(session, 400, "Total", "total", None)
    _add_series(session, 401, "Asia", "region", None)
    _add_series(session, 402, "Japan", "market", 401)

    regions = SeriesMaster.get_by_level(session, level="region")
    ids = [s.series_id for s in regions]
    assert 401 in ids
    assert all(s.level == "region" for s in regions)



# 5) get_by_level: ordered by name
def test_seriesmaster_get_by_level_is_ordered_by_name(session: Session):
    """Unit test. GIVEN multiple series in same level WHEN get_by_level THEN results are sorted by name."""
    _add_series(session, 500, "B-Region", "region", None)
    _add_series(session, 501, "A-Region", "region", None)

    regions = SeriesMaster.get_by_level(session, level="region")
    names = [r.name for r in regions]

    assert names == sorted(names)


# 6) Observation classmethod wrappers: entry points behave consistently
def test_observation_classmethods_match_analysis_functions(session: Session):
    """
    Unit test. GIVEN observations in DB WHEN calling Observation.* methods THEN results are returned (wrapper works).
    This ensures ORM class exposes analytical behaviour as required by CW2.
    """
    _add_series(session, 600, "Asia", "region", None)
    _add_series(session, 601, "Japan", "market", 600)

    _add_obs(session, 601, date(2023, 1, 1), 100.0)
    _add_obs(session, 601, date(2024, 1, 1), 120.0)

    yoy = Observation.yoy_change(session, 601, date(2024, 1, 1))
    ma = Observation.moving_average(session, 601, window=2)

    assert yoy == 20.0
    assert ma[0][1] is None  # first point has no window by your test semantics

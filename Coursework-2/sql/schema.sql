-- schema.sql
CREATE TABLE IF NOT EXISTS series_master (
    series_id INTEGER PRIMARY KEY,
    level INTEGER,
    name TEXT,
    parent_id INTEGER,
    full_path TEXT
);

CREATE TABLE IF NOT EXISTS observations (
    series_id INTEGER,
    date DATE,
    value REAL,
    month TEXT
);

CREATE INDEX IF NOT EXISTS idx_obs_series_date ON observations(series_id, date);

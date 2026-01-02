"""
example_queries.py
Runs example SQL queries on visitor_arrivals.db
"""

import sqlite3
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
DB = OUT / "visitor_arrivals.db"


def run_query(sql, outname):
    with sqlite3.connect(DB) as conn:
        df = pd.read_sql_query(sql, conn, parse_dates=["date"])
    df.to_csv(OUT / outname, index=False)
    print(f"Saved {outname} ({len(df)} rows)")


def main():
    q1 = """
    WITH md AS (SELECT MAX(date) AS md FROM observations)
    SELECT s.full_path, o.value, o.date
    FROM observations o
    JOIN series_master s ON s.series_id=o.series_id
    JOIN md ON o.date=md.md
    ORDER BY o.value DESC
    LIMIT 15;
    """
    run_query(q1, "sql_top15_latest.csv")

    q2 = """
    SELECT strftime('%Y-%m', o.date) AS month, s.name, SUM(o.value) AS total
    FROM observations o
    JOIN series_master s ON s.series_id=o.series_id
    WHERE s.level=0
    GROUP BY month, s.name
    ORDER BY month;
    """
    run_query(q2, "sql_monthly_totals.csv")


if __name__ == "__main__":
    main()

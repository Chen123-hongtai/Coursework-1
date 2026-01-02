"""
create_db.py
Builds SQLite database (outputs/visitor_arrivals.db)
"""

import pandas as pd
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
DB = OUT / "visitor_arrivals.db"


def main():
    meta = pd.read_csv(OUT / "series_master.csv")
    obs = pd.read_csv(OUT / "observations_long.csv", parse_dates=["date"])

    conn = sqlite3.connect(DB)
    meta.to_sql("series_master", conn, if_exists="replace", index=False)
    obs.to_sql("observations", conn, if_exists="replace", index=False)

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_obs_series_date
        ON observations(series_id, date);
        """
    )

    conn.commit()
    conn.close()

    print(f"Database created → {DB}")


if __name__ == "__main__":
    main()

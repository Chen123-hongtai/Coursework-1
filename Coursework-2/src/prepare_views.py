"""
prepare_views.py
Generates 3 audience-specific prepared views from observations_long.csv
and saves to outputs/.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def main():
    obs = pd.read_csv(OUT / "observations_long.csv", parse_dates=["date"])
    meta = pd.read_csv(OUT / "series_master.csv")
    df = obs.merge(meta, on="series_id")

    # Q1 – Regional comparison (level 1)
    q1 = (
        df[df["level"] == 1]
        .groupby(["name", df["date"].dt.year])
        .value.sum()
        .reset_index()
    )
    q1.to_csv(OUT / "prep_regional_comparison.csv", index=False)

    # Q2 – Rebound rate (2019 vs 2025)
    pivot = df.pivot_table(
        index="full_path",
        columns=df["date"].dt.year,
        values="value",
        aggfunc="sum",
    )

    for col in [2019, 2025]:
        if col not in pivot.columns:
            pivot[col] = None

    pivot["rebound_%"] = (pivot[2025] / pivot[2019] - 1) * 100
    pivot.reset_index().to_csv(
        OUT / "prep_rebound_by_market.csv",
        index=False,
    )

    # Q3 – Seasonality (rolling mean)
    def rolling_mean(x):
        """Return a 12-month rolling mean for each market."""
        return x.rolling(12, min_periods=6).mean()

    q3 = (
        df.groupby("full_path")[["date", "value"]]
        .apply(lambda g: g.set_index("date")["value"]
        .rolling(12, min_periods=6)
        .mean())
        .reset_index()
    )
    q3.rename(columns={"value": "rolling_mean"}, inplace=True)
    q3.to_csv(OUT / "prep_seasonality.csv", index=False)

    print("Three prepared views saved in outputs/.")


if __name__ == "__main__":
    main()

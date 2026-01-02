"""
explore_international_visitors.py
Loads parsed outputs and generates summary & visualizations.
"""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)


def main():
    meta = pd.read_csv(OUT / "series_master.csv")
    obs = pd.read_csv(OUT / "observations_long.csv", parse_dates=["date"])
    df = obs.merge(meta, on="series_id")

    latest = df["date"].max()
    latest_vals = df[df["date"] == latest]
    top10 = latest_vals.sort_values("value", ascending=False).head(10)
    top10.to_csv(OUT / "top10_latest.csv", index=False)
    print(f"Top 10 series for {latest.date()} saved → outputs/top10_latest.csv")

    # ---------- 1 Top-5 markets over time ----------
    top5 = top10["series_id"].head(5).tolist()
    pivot = (
        df[df["series_id"].isin(top5)]
        .pivot_table(index="date", columns="full_path", values="value", aggfunc="sum")
    )
    plt.figure(figsize=(10, 6))
    for col in pivot.columns:
        plt.plot(pivot.index, pivot[col], marker="o", label=col)
    plt.title("Top-5 Visitor Series Over Time")
    plt.xlabel("Date")
    plt.ylabel("Arrivals")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(OUT / "plot_top5_series.png")
    plt.close()
    print("Plot saved → outputs/plot_top5_series.png")

    # ---------- 2 Regional totals (level 1) ----------
    reg = (
        df[df["level"] == 1]
        .groupby(["date", "name"])
        .value.sum()
        .reset_index()
    )
    pivot_reg = reg.pivot(index="date", columns="name", values="value")
    pivot_reg.plot(figsize=(10, 6))
    plt.title("Regional Totals (Level 1) Over Time")
    plt.xlabel("Date")
    plt.ylabel("Arrivals")
    plt.tight_layout()
    plt.savefig(OUT / "plot_region_totals.png")
    plt.close()
    print("Plot saved → outputs/plot_region_totals.png")

    # ---------- 3 Seasonality heatmap ----------
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    monthly = (
        df.groupby(["month", "year"])["value"]
        .sum()
        .unstack("year")
        .fillna(0)
    )
    plt.figure(figsize=(12, 6))
    plt.imshow(monthly, aspect="auto", cmap="viridis")
    plt.colorbar(label="Total Arrivals")
    plt.title("Seasonality Heatmap – Total Arrivals by Month and Year")
    plt.xlabel("Year")
    plt.ylabel("Month (1–12)")
    plt.yticks(range(12), range(1, 13))
    plt.tight_layout()
    plt.savefig(OUT / "plot_seasonality_heatmap.png")
    plt.close()
    print("Plot saved → outputs/plot_seasonality_heatmap.png")

    # ---------- 4 Missing-data summary ----------
    miss = df.groupby("full_path")["value"].apply(lambda s: s.isna().sum())
    miss_ratio = (miss / len(df["date"].unique())) * 100
    miss_df = pd.DataFrame({"missing_count": miss, "missing_pct": miss_ratio})
    miss_df.sort_values("missing_pct", ascending=False).head(20).plot(
        kind="bar", figsize=(10, 6), legend=False
    )
    plt.title("Top 20 Series by Missing-Data Percentage")
    plt.ylabel("Missing (%)")
    plt.tight_layout()
    plt.savefig(OUT / "plot_missingness.png")
    plt.close()
    miss_df.to_csv(OUT / "missing_by_series.csv")
    print("Missingness summary and plot saved → outputs/missing_by_series.csv")

    # ---------- 5 Year-on-year totals ----------
    annual = df.groupby(df["date"].dt.year)["value"].sum().reset_index()
    plt.figure(figsize=(10, 6))
    plt.bar(annual["date"], annual["value"])
    plt.title("Total Annual Visitor Arrivals by Sea")
    plt.xlabel("Year")
    plt.ylabel("Arrivals")
    plt.tight_layout()
    plt.savefig(OUT / "plot_annual_totals.png")
    plt.close()
    print("Plot saved → outputs/plot_annual_totals.png")


if __name__ == "__main__":
    main()

"""
parse_international_visitors.py
Parses 'InternationalVisitorArrivalsByInboundTourismMarketsSeaMonthly.csv' —
a hierarchical monthly dataset of visitor arrivals by country/region.

Outputs:
 - outputs/series_master.csv
 - outputs/observations_long.csv
"""

from pathlib import Path
import pandas as pd
import numpy as np
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'
OUT.mkdir(exist_ok=True)

FILE = DATA / 'InternationalVisitorArrivalsByInboundTourismMarketsSeaMonthly.csv'


def detect_indent_level(name: str):
    """Estimate hierarchy level from leading spaces."""
    m = re.match(r"^([\s\t]*)(.*)", str(name))
    lead, core = m.group(1), m.group(2).strip()
    spaces, tabs = lead.count(" "), lead.count("\t")
    return tabs + (spaces // 4), core


def parse_dataset(df):
    series_meta, observations = [], []
    parent_stack, next_id = {}, 1
    months = df.columns[1:].tolist()

    for _, row in df.iterrows():
        rawname = str(row.iloc[0])
        if not rawname.strip():
            continue

        level, name = detect_indent_level(rawname)
        parent_id = parent_stack.get(level - 1) if level > 0 else None

        series_id = next_id
        next_id += 1

        # Build full path using stack
        path_parts = [
            s["name"]
            for indent_level, s in [(s["level"], s) for s in series_meta]
            if indent_level < level and s["series_id"] in parent_stack.values()
        ]
        path_parts.append(name)
        full_path = " > ".join(path_parts)

        meta = {
            "series_id": series_id,
            "level": level,
            "name": name,
            "parent_id": parent_id,
            "full_path": full_path,
        }
        series_meta.append(meta)

        parent_stack[level] = series_id
        # remove deeper
        for indent_level in [x for x in parent_stack.keys() if x > level]:
            del parent_stack[indent_level]

        # Monthly values
        for m in months:
            val = str(row[m]).strip()
            if val in ("", "N/A", "NA", "-", "nan"):
                num = np.nan
            else:
                try:
                    num = float(val.replace(",", ""))
                except ValueError:
                    num = np.nan
            observations.append({"series_id": series_id, "month": m, "value": num})

    return pd.DataFrame(series_meta), pd.DataFrame(observations)


def convert_month_to_date(obs_df):
    """Convert columns like 2025May to datetime (first of month)."""
    def to_date(lbl):
        try:
            return pd.to_datetime(lbl, format="%Y%b")
        except Exception:
            try:
                return pd.to_datetime(lbl, format="%Y%B")
            except Exception:
                return pd.NaT

    obs_df["date"] = obs_df["month"].apply(to_date)
    obs_df = obs_df.dropna(subset=["date"])
    return obs_df


def main():
    if not FILE.exists():
        print(f"File not found: {FILE}")
        return

    df = pd.read_csv(FILE)
    meta, obs = parse_dataset(df)
    obs = convert_month_to_date(obs)

    meta.to_csv(OUT / "series_master.csv", index=False)
    obs.to_csv(OUT / "observations_long.csv", index=False)

    print("Saved:")
    print(" - outputs/series_master.csv")
    print(" - outputs/observations_long.csv")
    print(f"{len(meta)} series, {len(obs)} monthly observations.")


if __name__ == "__main__":
    main()

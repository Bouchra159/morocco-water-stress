"""
measure_rainfall.py
Annual rainfall near home (Taroudant, Souss-Massa), 1990-2024, from NASA POWER —
the long, honest climate signal behind the drying south.

Rainfall is the *driver*: the land's greenness, the farms, and whether families can
stay all follow the rain. A 35-year record is long enough to see a real trend, not
just weather. Source: NASA POWER (satellite + reanalysis), open, no account.

Outputs: data/processed/rainfall_taroudant.csv, figures/fig_rainfall_trend.png
"""
from __future__ import annotations
import calendar
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

LAT, LON = 30.47, -8.88          # Taroudant, in the Souss valley
START, END = 1990, 2025
POWER = "https://power.larc.nasa.gov/api/temporal/monthly/point"

WATER = "#2a6f97"; CRISIS = "#b3261e"; INK = "#1a1a1a"; GREY = "#8a8a8a"


def annual_rainfall() -> pd.DataFrame:
    r = requests.get(POWER, params={"parameters": "PRECTOTCORR", "community": "AG",
                     "longitude": LON, "latitude": LAT, "start": START, "end": END,
                     "format": "JSON"}, timeout=90).json()
    monthly = r["properties"]["parameter"]["PRECTOTCORR"]
    totals: dict[int, float] = {}
    for key, val in monthly.items():
        if key.endswith("13") or val < -900:     # skip annual code / fill
            continue
        year, month = int(key[:4]), int(key[4:6])
        totals[year] = totals.get(year, 0.0) + val * calendar.monthrange(year, month)[1]
    return pd.DataFrame({"year": sorted(totals), "rainfall_mm": [round(totals[y], 1) for y in sorted(totals)]})


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    df = annual_rainfall()
    df.to_csv(PROCESSED / "rainfall_taroudant.csv", index=False)

    mean = df["rainfall_mm"].mean()
    z = np.polyfit(df["year"], df["rainfall_mm"], 1)
    roll = df["rainfall_mm"].rolling(5, center=True).mean()

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ["tab:red" if v < 0.7 * mean else "tab:blue" for v in df["rainfall_mm"]]
    ax.bar(df["year"], df["rainfall_mm"], color=colors, label="annual rainfall")
    ax.axhline(mean, color="gray", linestyle="--", linewidth=1,
               label=f"{START}–{END} average ({mean:.0f} mm)")
    ax.plot(df["year"], np.poly1d(z)(df["year"]), color="black", linewidth=1.5,
            label=f"trend: {z[0]*10:+.0f} mm/decade")
    ax.plot(df["year"], roll, color="orange", linewidth=2, label="5-year average")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual rainfall (mm)")
    ax.set_title(f"Annual rainfall near Taroudant, {START}–{END} (NASA POWER)")
    ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "fig_rainfall_trend.png", dpi=150); plt.close(fig)

    recent = df[df["year"] >= 2015]["rainfall_mm"].mean()
    early = df[df["year"] < 2000]["rainfall_mm"].mean()
    print(df.to_string(index=False))
    print(f"\nmean {mean:.0f} mm | trend {z[0]*10:+.1f} mm/decade")
    print(f"pre-2000 avg {early:.0f} mm  ->  2015+ avg {recent:.0f} mm  "
          f"({100*(recent-early)/early:+.0f}%)")
    print("wrote figures/fig_rainfall_trend.png")


if __name__ == "__main__":
    main()

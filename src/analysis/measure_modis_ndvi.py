"""
measure_modis_ndvi.py
A 25-year vegetation-greenness record (2000-2026) for the argan region near
Taroudant, from MODIS MOD13Q1 (250 m, 16-day NDVI).

Why: the Sentinel-2 record only starts in 2015, so nine years is too short to
prove a long-term trend. MODIS reaches back to 2000 — a quarter-century — which is
long enough to separate a real trend from year-to-year rainfall swings.

Data source: ORNL MODIS Web Service (modis.ornl.gov) — no login required, so the
whole pipeline stays reproducible by anyone. (NASA's `earthaccess` library is the
scalable cloud-native alternative, but it needs an Earthdata Login.)

Outputs: data/processed/modis_ndvi_argan.csv, figures/fig_modis_ndvi_trend.png
"""
from __future__ import annotations
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

BASE = "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset"
LAT, LON = 30.2, -8.5            # argan / Anti-Atlas slopes near Taroudant
BAND = "250m_16_days_NDVI"
FILL = -2000                    # values below this are fill / cloud
START_YEAR, END_YEAR = 2000, 2026


def fetch_chunk(year: int, doy0: int, doy1: int) -> list[tuple[str, float]]:
    # ORNL caps each /subset request to ~10 composites, so keep chunks short
    params = {"latitude": LAT, "longitude": LON,
              "startDate": f"A{year}{doy0:03d}", "endDate": f"A{year}{doy1:03d}",
              "kmAboveBelow": 1, "kmLeftRight": 1, "band": BAND}
    r = requests.get(BASE, params=params, headers={"Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    out = []
    for s in r.json().get("subset", []):
        vals = np.array(s["data"], dtype=float)
        vals = vals[vals > FILL]
        if vals.size:
            out.append((s["calendar_date"], float(vals.mean()) * 0.0001))
    return out


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    rows = []
    for y in range(START_YEAR, END_YEAR + 1):
        for d0 in (1, 129, 257):                     # ~4-month chunks (<=8 composites)
            d1 = min(d0 + 127, 366)
            try:
                rows += fetch_chunk(y, d0, d1)
            except Exception as e:
                print(f"chunk {y} doy{d0} failed:", e)
            time.sleep(0.25)
        print(f"through {y}: {len(rows)} obs")

    df = pd.DataFrame(rows, columns=["date", "ndvi"]).drop_duplicates("date")
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    annual = df.groupby("year")["ndvi"].mean().reset_index()
    annual = annual[(annual["year"] >= START_YEAR) & (annual["year"] <= END_YEAR)]
    annual.to_csv(PROCESSED / "modis_ndvi_argan.csv", index=False)

    z = np.polyfit(annual["year"], annual["ndvi"], 1)
    roll = annual["ndvi"].rolling(5, center=True).mean()

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(annual["year"], annual["ndvi"], marker="o", label="annual mean NDVI")
    ax.plot(annual["year"], np.poly1d(z)(annual["year"]), color="black", linestyle="--",
            label=f"trend: {z[0]*10:+.3f} NDVI/decade")
    ax.plot(annual["year"], roll, color="orange", linewidth=2, label="5-year average")
    ax.set_xlabel("Year")
    ax.set_ylabel("Annual mean NDVI")
    ax.set_title("Vegetation greenness on the argan slopes near Taroudant, 2000–2026 (MODIS)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig_modis_ndvi_trend.png", dpi=150)
    plt.close(fig)

    early = annual[annual["year"] <= 2005]["ndvi"].mean()
    recent = annual[annual["year"] >= 2021]["ndvi"].mean()
    print(annual.to_string(index=False))
    print(f"\n{len(df)} MODIS observations, {len(annual)} years")
    print(f"trend {z[0]*10:+.4f} NDVI/decade | 2000-05 avg {early:.3f} -> 2021-26 avg {recent:.3f} "
          f"({100*(recent-early)/early:+.0f}%)")
    print("wrote figures/fig_modis_ndvi_trend.png")


if __name__ == "__main__":
    main()

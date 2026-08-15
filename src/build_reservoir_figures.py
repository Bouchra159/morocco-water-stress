"""
build_reservoir_figures.py
Run the 10-year Al Massira measurement and build its two figures:
  fig6_reservoir_area_timeseries.png   water surface area 2016-2025
  fig7_reservoir_masks_grid.png        small-multiples of the shrinking reservoir

Depends on src/measure_reservoir.py. Re-uses cached results in data/processed
if present (reservoir_area.csv + reservoir_masks.npz) so re-plotting is instant.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import measure_reservoir as mr  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

CALM = "#2a6f97"
CRISIS = "#b3261e"
INK = "#1a1a1a"
GREY = "#8a8a8a"


def get_data(force: bool = False):
    csv = PROCESSED / "reservoir_area.csv"
    npz = PROCESSED / "reservoir_masks.npz"
    if csv.exists() and npz.exists() and not force:
        df = pd.read_csv(csv)
        if set(df["year"]) >= set(mr.YEARS):
            z = np.load(npz)
            masks = {int(k): z[k] for k in z.files}
            return df.sort_values("year").reset_index(drop=True), masks
    df, masks = mr.main(mr.YEARS)
    return df.sort_values("year").reset_index(drop=True), masks


def fig_timeseries(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.fill_between(df["year"], df["water_area_km2"], color=CALM, alpha=0.15)
    ax.plot(df["year"], df["water_area_km2"], color=CALM, lw=2.6,
            marker="o", ms=5)

    peak = df.loc[df["water_area_km2"].idxmax()]
    trough = df.loc[df["water_area_km2"].idxmin()]
    for row, dy, col in [(peak, 14, CALM), (trough, 14, CRISIS)]:
        ax.annotate(f"{row['water_area_km2']:.0f} km²\n{int(row['year'])}",
                    (row["year"], row["water_area_km2"]),
                    textcoords="offset points", xytext=(0, dy),
                    ha="center", fontsize=10, fontweight="bold", color=col)
    drop = 100 * (1 - trough["water_area_km2"] / peak["water_area_km2"])
    ax.text(0.98, 0.9, f"−{drop:.0f}% water surface",
            transform=ax.transAxes, ha="right", fontsize=13,
            fontweight="bold", color=CRISIS)

    ax.set_title("Al Massira reservoir has almost vanished from space",
                 fontsize=13, fontweight="bold", color=INK, loc="left")
    ax.set_ylabel("Water surface area (km²)")
    ax.set_ylim(0, df["water_area_km2"].max() * 1.2)
    ax.grid(True, color="#eeeeee")
    ax.set_axisbelow(True)
    fig.text(0.125, -0.02,
             "Measured from Sentinel-2 (NDWI + Otsu), dry-season scenes, tile 29SPR. "
             "Data: Earth Search / Sentinel-2 L2A.",
             fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig6_reservoir_area_timeseries.png", bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/fig6_reservoir_area_timeseries.png")


def fig_masks_grid(df: pd.DataFrame, masks: dict) -> None:
    years = sorted(masks)
    n = len(years)
    cols = 5
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(2.4 * cols, 2.6 * rows))
    axes = np.atleast_1d(axes).ravel()
    area_by_year = dict(zip(df["year"], df["water_area_km2"]))
    for ax, y in zip(axes, years):
        ax.imshow(masks[y], cmap="Blues", interpolation="nearest", vmin=0, vmax=1)
        a = area_by_year.get(y, np.nan)
        col = CRISIS if a < 30 else INK
        ax.set_title(f"{y} — {a:.0f} km²", fontsize=10, color=col, fontweight="bold")
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor("#dddddd")
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle("Al Massira reservoir water extent, 2016–2025 (Sentinel-2)",
                 fontsize=14, fontweight="bold", color=INK, y=1.01)
    fig.text(0.5, -0.01,
             "Blue = open water (NDWI + Otsu). Same footprint each year. "
             "Data: Sentinel-2 L2A via Earth Search.",
             ha="center", fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig7_reservoir_masks_grid.png", bbox_inches="tight", dpi=140)
    plt.close(fig)
    print("wrote figures/fig7_reservoir_masks_grid.png")


def main() -> None:
    df, masks = get_data()
    print(df.to_string(index=False))
    fig_timeseries(df)
    fig_masks_grid(df, masks)


if __name__ == "__main__":
    main()

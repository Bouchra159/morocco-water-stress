"""
build_method_figures.py
Two teaching figures that show *how* the reservoir measurement works — built from
the real data, so they double as evidence of understanding:

  fig_method_ndwi_otsu.png   a real NDWI histogram with the Otsu split
  fig_method_area_volume.png why surface area falls slower than volume

Depends on src/measure_reservoir.py (uses the same NDWI + Otsu code).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import measure_reservoir as mr

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"

WATER = "#2a6f97"
LAND = "#c9a15a"
CRISIS = "#b3261e"
INK = "#1a1a1a"
GREY = "#8a8a8a"

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150, "font.size": 11,
                     "axes.edgecolor": "#cccccc"})


def ndwi_otsu_figure(year: int = 2018) -> None:
    """Real NDWI histogram from one scene, with the automatic Otsu threshold."""
    feat = mr.best_scene(year)
    _water, ndwi, date, _cloud = mr.water_mask_for(feat)
    vals = ndwi[np.isfinite(ndwi)]
    thr = max(mr.otsu(vals), 0.0)

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.hist(vals, bins=140, range=(-0.6, 0.6), color="#d9d2c4", edgecolor="none")
    ax.set_yscale("log")  # so the small water peak is visible next to all the land
    ax.axvline(thr, color=CRISIS, lw=2)
    ax.text(thr + 0.01, ax.get_ylim()[1] * 0.4,
            f"Otsu threshold\nNDWI = {thr:.2f}", color=CRISIS, fontsize=10, fontweight="bold")

    ax.annotate("LAND\n(dry, low NDWI)", xy=(-0.3, 1), xytext=(-0.45, ax.get_ylim()[1] * 0.06),
                color=LAND, fontsize=11, fontweight="bold", ha="center")
    ax.annotate("WATER\n(high NDWI)", xy=(0.3, 1), xytext=(0.36, ax.get_ylim()[1] * 0.02),
                color=WATER, fontsize=11, fontweight="bold", ha="center")
    ax.axvspan(thr, 0.6, color=WATER, alpha=0.06)

    ax.set_title(f"Why an automatic threshold: one scene's own NDWI histogram ({date})",
                 fontsize=12.5, fontweight="bold", color=INK, loc="left")
    ax.set_xlabel("NDWI  (water is high, land is low)")
    ax.set_ylabel("number of pixels (log scale)")
    fig.text(0.125, -0.02,
             "The image contains two populations — land and water. Otsu finds the split "
             "between them from the data itself, so it adapts to each scene instead of "
             "trusting a fixed guess.", fontsize=8.5, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig_method_ndwi_otsu.png", bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/fig_method_ndwi_otsu.png  (Otsu =", round(thr, 3), ")")


def area_volume_figure() -> None:
    """Schematic: as the level drops, surface width shrinks slower than stored volume."""
    x = np.linspace(-1, 1, 400)
    floor = x ** 2               # a simple bowl-shaped valley cross-section
    full, low = 0.9, 0.35

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.6), sharey=True)
    for ax, level, label, col in [(axes[0], full, "Full reservoir", WATER),
                                  (axes[1], low, "Low reservoir", CRISIS)]:
        ax.fill_between(x, floor, 3, color="#efe7d8")            # the hills
        ax.plot(x, floor, color="#8a6f45", lw=1.5)
        wx = x[floor <= level]
        ax.fill_between(wx, floor[floor <= level], level, color=WATER, alpha=.85)
        # surface width marker
        ax.annotate("", xy=(wx.min(), level + .06), xytext=(wx.max(), level + .06),
                    arrowprops=dict(arrowstyle="<->", color=col, lw=1.6))
        ax.text(0, level + .12, "surface area", ha="center", color=col, fontsize=10, fontweight="bold")
        ax.set_title(label, color=INK, fontweight="bold")
        ax.set_xlim(-1.1, 1.1); ax.set_ylim(0, 1.5)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)

    fig.suptitle("Surface area falls slower than volume — so 91% area loss means the volume loss is worse",
                 fontsize=12.5, fontweight="bold", color=INK, y=1.02)
    fig.text(0.5, -0.03,
             "As the water level drops, the reservoir narrows toward its deepest channel. "
             "The surface you can measure from space shrinks — but the water you've actually "
             "lost shrinks faster. Measuring area is the honest, conservative choice.",
             ha="center", fontsize=8.5, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig_method_area_volume.png", bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/fig_method_area_volume.png")


def main() -> None:
    FIG.mkdir(exist_ok=True)
    ndwi_otsu_figure(2018)
    area_volume_figure()


if __name__ == "__main__":
    main()

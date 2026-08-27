"""
build_reservoir_gif.py
Animate the Al Massira reservoir vanishing, 2017-2025, from the Sentinel-2 masks.

Each frame shows the 2017 full pool as a pale "ghost" with the current year's
open water filled in on top — so the eye watches the blue drain away against the
shape of what used to be there. Output: figures/reservoir_timelapse.gif
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

EARTH = np.array([0.92, 0.87, 0.78])   # dry lakebed tan
GHOST = np.array([0.80, 0.88, 0.92])   # pale 2017 full-pool
WATER = np.array([0.10, 0.42, 0.56])   # deep water blue
INK = "#241c14"
CRISIS = "#b3261e"
WBLUE = "#1a6a8f"


def main() -> None:
    z = np.load(PROCESSED / "reservoir_masks.npz")
    years = sorted(int(k) for k in z.files)
    masks = {y: z[str(y)].astype(bool) for y in years}
    areas = pd.read_csv(PROCESSED / "reservoir_area.csv").set_index("year")["water_area_km2"].to_dict()

    ghost = masks[min(years)]
    ys, xs = np.where(ghost)
    pad = 25
    y0, y1 = max(0, ys.min() - pad), min(ghost.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(ghost.shape[1], xs.max() + pad)
    g = ghost[y0:y1, x0:x1]
    aspect = g.shape[0] / g.shape[1]

    frames = []
    for y in years:
        gg = ghost[y0:y1, x0:x1]
        ww = masks[y][y0:y1, x0:x1]
        img = np.ones((*gg.shape, 3)) * EARTH
        img[gg] = GHOST
        img[ww] = WATER

        fig = plt.figure(figsize=(7, 7 * aspect), dpi=115)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(img, interpolation="bilinear")
        ax.axis("off")
        a = areas.get(y, float("nan"))
        ax.text(0.035, 0.95, "Al Massira reservoir", transform=ax.transAxes,
                fontsize=17, fontweight="bold", color=INK, va="top")
        ax.text(0.035, 0.86, f"{y}", transform=ax.transAxes,
                fontsize=34, fontweight="bold", color=WBLUE, va="top")
        ax.text(0.035, 0.045, f"{a:.0f} km² of open water",
                transform=ax.transAxes, fontsize=15, fontweight="bold",
                color=CRISIS if a < 30 else INK, va="bottom")
        ax.text(0.965, 0.045, "Sentinel-2  ·  NDWI", transform=ax.transAxes,
                fontsize=9, color="#7d715f", va="bottom", ha="right")

        buf = BytesIO()
        fig.savefig(buf, format="png", facecolor="white")
        plt.close(fig)
        frames.append(Image.open(buf).convert("RGB"))

    # normalise to identical size, then quantise for GIF
    w, h = frames[0].size
    frames = [f.resize((w, h)).convert("P", palette=Image.ADAPTIVE, colors=64) for f in frames]

    durations = [1000] * len(frames)
    durations[0] = 1500
    durations[-1] = 2800
    out = FIG / "reservoir_timelapse.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, disposal=2, optimize=True)
    print("wrote", out.relative_to(ROOT), f"({out.stat().st_size // 1024} KB, {len(frames)} frames)")


if __name__ == "__main__":
    main()

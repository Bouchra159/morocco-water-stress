"""
fetch_truecolor.py
Two aligned true-colour Sentinel-2 crops of the Al Massira reservoir — 2017 (full)
and 2024 (near-empty) — for an interactive before/after swipe, the NASA Earth
Observatory / NYT technique for showing environmental change.

Same footprint and pixel grid both years so the slider lines up.
Output: figures/truecolor_2017.jpg, figures/truecolor_2024.jpg
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import numpy as np
import rasterio
from PIL import Image
from pyproj import Transformer
from rasterio.windows import from_bounds

import measure_reservoir as mr

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
AOI = (-7.78, 32.40, -7.40, 32.63)   # reservoir bounding box (lon/lat)
SCALE = 2                            # 10 m -> 20 m for a web-sized crop


def stretch(band: np.ndarray, lo=2, hi=98) -> np.ndarray:
    v = band[np.isfinite(band) & (band > 0)]
    p1, p2 = np.percentile(v, [lo, hi])
    out = np.clip((band - p1) / (p2 - p1 + 1e-6), 0, 1)
    return (out * 255).astype("uint8")


def read_rgb(year: int) -> Image.Image:
    feat = mr.best_scene(year)
    hrefs = [feat["assets"][b]["href"] for b in ("red", "green", "blue")]
    with rasterio.open(hrefs[0]) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (int(win.height // SCALE), int(win.width // SCALE))
    chans = [stretch(mr.read_band(h, win, out_shape)) for h in hrefs]
    rgb = np.dstack(chans)
    print(f"{year}: {feat['properties']['datetime'][:10]}  {rgb.shape}")
    return Image.fromarray(rgb, "RGB")


def main() -> None:
    FIG.mkdir(exist_ok=True)
    for year in (2017, 2024):
        img = read_rgb(year)
        img.save(FIG / f"truecolor_{year}.jpg", quality=88, optimize=True)
        print(f"wrote figures/truecolor_{year}.jpg")


if __name__ == "__main__":
    main()

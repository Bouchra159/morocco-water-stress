"""
measure_reservoir.py
Measure the Al Massira reservoir's water surface area from Sentinel-2, 2016-2025.

Method (grounded in the published remote-sensing literature on this reservoir):
  1. For each year, take the least-cloudy Sentinel-2 L2A scene in the dry season
     (Aug 1 - Oct 15) over MGRS tile 29SPR, which contains the reservoir.
  2. Compute NDWI = (green - NIR) / (green + NIR)  (McFeeters 1996).
  3. Separate water from land with an automatic Otsu threshold.
  4. Mask out cloud / shadow pixels using the scene classification (SCL) band.
  5. Water area = water pixels x pixel area.

Data: Sentinel-2 L2A COGs via the open Earth Search STAC API (no account needed).
Outputs: data/processed/reservoir_area.csv, figures/fig6_*, figures/fig7_*.

Reference method: NDWI + automatic thresholding for reservoir surface-water
monitoring, e.g. studies of Al Massira / Mediterranean reservoirs (2023-2025).
"""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "3")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "1")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import rasterio
import requests
from rasterio.windows import from_bounds
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

STAC = "https://earth-search.aws.element84.com/v1/search"
TILE = "MGRS-29SPR"
AOI = (-7.80, 32.38, -7.34, 32.64)   # reservoir bounding box (lon/lat)
YEARS = list(range(2016, 2027))
SCALE = 3                            # 10 m -> 30 m read for speed
PX_AREA_KM2 = (10 * SCALE) ** 2 / 1e6
SCL_BAD = {3, 8, 9, 10}             # cloud shadow, cloud med/high, cirrus


def best_scene(year: int):
    """Least-cloudy dry-season scene on tile 29SPR for a given year."""
    r = requests.post(STAC, json={
        "collections": ["sentinel-2-l2a"],
        "bbox": list(AOI),
        "datetime": f"{year}-08-01T00:00:00Z/{year}-10-15T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 20}, "grid:code": {"eq": TILE}},
        "limit": 40,
    }, timeout=40).json()
    feats = [f for f in r.get("features", [])
             if (f["properties"].get("grid:code") == TILE)]
    if not feats:
        return None
    feats.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return feats[0]


def read_band(href, win, out_shape, resampling=rasterio.enums.Resampling.nearest):
    with rasterio.open(href) as src:
        return src.read(1, window=win, out_shape=out_shape,
                        resampling=resampling).astype("float32")


def otsu(x: np.ndarray) -> float:
    x = x[np.isfinite(x)]
    hist, edges = np.histogram(x, bins=256)
    centers = (edges[:-1] + edges[1:]) / 2
    w = hist.astype(float)
    total = w.sum()
    wB = np.cumsum(w)
    wF = total - wB
    with np.errstate(invalid="ignore", divide="ignore"):
        mB = np.cumsum(w * centers) / np.maximum(wB, 1)
        mF = np.cumsum((w * centers)[::-1])[::-1] / np.maximum(wF, 1)
    between = wB * wF * (mB - mF) ** 2
    return float(centers[np.argmax(between)])


def water_mask_for(feat):
    """Return (water_mask, ndwi, date, cloud) for a scene."""
    green_href = feat["assets"]["green"]["href"]
    nir_href = feat["assets"]["nir"]["href"]
    scl_href = feat["assets"]["scl"]["href"]

    with rasterio.open(green_href) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (int(win.height // SCALE), int(win.width // SCALE))

    green = read_band(green_href, win, out_shape)
    nir = read_band(nir_href, win, out_shape)
    scl = read_band(scl_href, win, out_shape)  # 20 m, resampled to grid

    filled = (green > 0) & (nir > 0)
    cloud = np.isin(scl.astype(int), list(SCL_BAD))
    valid = filled & ~cloud

    ndwi = np.where(green + nir > 0, (green - nir) / (green + nir + 1e-6), np.nan)
    thr = max(otsu(ndwi[valid]), 0.0)
    water = (ndwi > thr) & valid
    return water, ndwi, feat["properties"]["datetime"][:10], \
        feat["properties"]["eo:cloud_cover"]


def main(years=None):
    years = years or YEARS
    FIG.mkdir(exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    rows, masks = [], {}
    for y in years:
        feat = best_scene(y)
        if feat is None:
            print(f"{y}: no scene")
            continue
        water, ndwi, date, cloud = water_mask_for(feat)
        area = float(water.sum()) * PX_AREA_KM2
        rows.append({"year": y, "date": date, "cloud_cover": round(cloud, 1),
                     "water_area_km2": round(area, 1)})
        masks[y] = water
        print(f"{y}: {date}  cloud={cloud:>4.1f}%  water={area:6.1f} km2")

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "reservoir_area.csv", index=False)
    print("wrote data/processed/reservoir_area.csv")
    np.savez_compressed(PROCESSED / "reservoir_masks.npz",
                        **{str(y): m for y, m in masks.items()})
    return df, masks


if __name__ == "__main__":
    main()

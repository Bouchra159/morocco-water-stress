"""
measure_crop_stress.py
Crop water stress on the Doukkala irrigated plain — the farmland that Al Massira
waters — measured from Sentinel-2, 2017-2026.

This closes the loop: the reservoir feeds ~96,000 ha of Doukkala farmland, so if
the dam runs dry, the crops should show it. Index: NDMI (Normalized Difference
Moisture Index) = (NIR - SWIR) / (NIR + SWIR) — high where vegetation is well
watered, low under moisture stress. Growing-season (Feb-Apr) scenes, cloud-masked.

Same open, no-login pipeline as the rest of the repo (Sentinel-2 via Earth Search).
The technique mirrors GEE crop-water-stress tutorials, done reproducibly without GEE.

Outputs: data/processed/crop_stress_doukkala.csv,
         figures/fig_crop_stress_trend.png, figures/map_crop_stress_change.png
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
import requests
from affine import Affine
from pyproj import Transformer
from rasterio.windows import from_bounds, transform as win_transform

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
GEO = ROOT / "data" / "geo"
FIG = ROOT / "figures"

STAC = "https://earth-search.aws.element84.com/v1/search"
TILE = "MGRS-29SNR"
AOI = (-8.60, 32.40, -8.35, 32.62)     # Doukkala irrigated plain (Zemamra / El Gharbia), solidly in 29SNR
YEARS = list(range(2017, 2027))
SCALE = 3
SCL_BAD = {3, 8, 9, 10}


def candidate_scenes(year):
    r = requests.post(STAC, json={
        "collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-02-01T00:00:00Z/{year}-04-15T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 25}, "grid:code": {"eq": TILE}}, "limit": 40},
        timeout=40).json()
    feats = [f for f in r.get("features", []) if f["properties"].get("grid:code") == TILE]
    feats.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return feats


def read_band(href, win, out_shape):
    with rasterio.open(href) as src:
        return src.read(1, window=win, out_shape=out_shape).astype("float32")


def ndmi_array(feat, want_transform=False):
    nir_h, swir_h, scl_h = (feat["assets"][b]["href"] for b in ("nir", "swir16", "scl"))
    with rasterio.open(nir_h) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (int(win.height // SCALE), int(win.width // SCALE))
        base_t = win_transform(win, src.transform) * Affine.scale(SCALE, SCALE)
        crs = src.crs
    nir = read_band(nir_h, win, out_shape)
    swir = read_band(swir_h, win, out_shape)
    scl = read_band(scl_h, win, out_shape)
    valid = (nir > 0) & (swir > 0) & ~np.isin(scl.astype(int), list(SCL_BAD))
    ndmi = np.where(nir + swir > 0, (nir - swir) / (nir + swir + 1e-6), np.nan)
    ndmi[~valid] = np.nan
    if want_transform:
        return ndmi, base_t, crs
    return ndmi


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    GEO.mkdir(parents=True, exist_ok=True)
    rows, arrays, transforms = [], {}, {}
    for y in YEARS:
        picked = None
        for feat in candidate_scenes(y):          # use the first scene that actually covers the AOI
            nd, tr, crs = ndmi_array(feat, want_transform=True)
            if np.isfinite(nd).mean() > 0.2:
                picked = (feat, nd)
                transforms[y] = (tr, crs)
                break
        if picked is None:
            print(f"{y}: no covering scene"); continue
        feat, nd = picked
        rows.append({"year": y, "date": feat["properties"]["datetime"][:10],
                     "cloud": round(feat["properties"]["eo:cloud_cover"], 1),
                     "mean_ndmi": round(float(np.nanmean(nd)), 4)})
        arrays[y] = nd
        print(f"{y}: {rows[-1]['date']} cloud={rows[-1]['cloud']:>4}  mean NDMI={rows[-1]['mean_ndmi']}")

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "crop_stress_doukkala.csv", index=False)

    # trend chart (plain)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["year"], df["mean_ndmi"], marker="o", color="tab:green", label="mean crop moisture (NDMI)")
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean NDMI  (higher = better watered)")
    ax.set_title("Crop water status on the Doukkala plain (fed by Al Massira), 2017–2026")
    ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "fig_crop_stress_trend.png", dpi=150); plt.close(fig)
    print("wrote figures/fig_crop_stress_trend.png")

    # change map: drought low (2024) -> recovery (2026)
    y0 = 2024 if 2024 in arrays else min(arrays)
    y1 = 2026 if 2026 in arrays else max(arrays)
    a0, a1 = arrays[y0], arrays[y1]
    hh, ww = min(a0.shape[0], a1.shape[0]), min(a0.shape[1], a1.shape[1])
    diff = a1[:hh, :ww] - a0[:hh, :ww]

    # export GeoTIFFs so the analysis can be styled in QGIS / ArcGIS Pro
    tr, crs = transforms.get(y1, (None, None))
    if tr is not None:
        for arr, fn in [(a1[:hh, :ww], f"crop_ndmi_{y1}.tif"), (diff, "crop_stress_change.tif")]:
            with rasterio.open(GEO / fn, "w", driver="GTiff", height=hh, width=ww, count=1,
                               dtype="float32", crs=crs, transform=tr, nodata=np.nan,
                               compress="deflate") as dst:
                dst.write(arr.astype("float32"), 1)
        print(f"wrote data/geo/crop_ndmi_{y1}.tif and crop_stress_change.tif")

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(diff, cmap="BrBG", vmin=-0.3, vmax=0.3,
                   extent=(AOI[0], AOI[2], AOI[1], AOI[3]), origin="upper")
    ax.set_title(f"Change in crop moisture (NDMI), Doukkala plain {y0}→{y1}")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("NDMI change  (green = wetter / recovered crops)")
    fig.tight_layout(); fig.savefig(FIG / "map_crop_stress_change.png", dpi=150); plt.close(fig)
    print("wrote figures/map_crop_stress_change.png")

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()

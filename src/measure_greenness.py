"""
measure_greenness.py
Measure the spring vegetation greenness (NDVI) of the argan / Anti-Atlas slopes
near home, 2017-2025, from Sentinel-2 — the same honest, reproducible method used
for the Al Massira reservoir, pointed at the land instead of the water.

NDVI = (NIR - Red) / (NIR + Red): high where vegetation is green and healthy.
We take one low-cloud spring scene (mid-Mar to end-May) per year, on the same
tile (29RNP), cloud-masked with SCL, and average NDVI over a fixed natural-veg
AOI in the argan belt (away from the irrigated valley floor).

Honesty note: nine years of optical data is a short record, and spring greenness
tracks each winter's rain. This measures *how green the land got each spring* — a
real, verifiable signal — not a proof of permanent climate change on its own.

Outputs: data/processed/greenness_argan.csv,
         figures/fig_greenness_trend.png, figures/fig_greenness_change.png
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
from pyproj import Transformer
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

STAC = "https://earth-search.aws.element84.com/v1/search"
TILE = "MGRS-29RNP"
AOI = (-8.65, 30.05, -8.35, 30.35)     # argan / Anti-Atlas slopes near Taroudant
YEARS = list(range(2017, 2027))
SCALE = 3                              # 10 m -> 30 m
SCL_BAD = {3, 8, 9, 10}               # cloud shadow, cloud med/high, cirrus

INK = "#1a1a1a"; GREEN = "#4a7a3a"; BROWN = "#a9683a"; GREY = "#8a8a8a"


def best_spring_scene(year: int):
    r = requests.post(STAC, json={
        "collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-03-15T00:00:00Z/{year}-05-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 20}, "grid:code": {"eq": TILE}},
        "limit": 40}, timeout=40).json()
    feats = [f for f in r.get("features", []) if f["properties"].get("grid:code") == TILE]
    if not feats:
        return None
    feats.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return feats[0]


def read_band(href, win, out_shape):
    with rasterio.open(href) as src:
        return src.read(1, window=win, out_shape=out_shape).astype("float32")


def ndvi_array(feat):
    red_h, nir_h, scl_h = (feat["assets"][b]["href"] for b in ("red", "nir", "scl"))
    with rasterio.open(red_h) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (int(win.height // SCALE), int(win.width // SCALE))
    red = read_band(red_h, win, out_shape)
    nir = read_band(nir_h, win, out_shape)
    scl = read_band(scl_h, win, out_shape)
    valid = (red > 0) & (nir > 0) & ~np.isin(scl.astype(int), list(SCL_BAD))
    ndvi = np.where(red + nir > 0, (nir - red) / (nir + red + 1e-6), np.nan)
    ndvi[~valid] = np.nan
    return ndvi


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    rows, arrays = [], {}
    for y in YEARS:
        feat = best_spring_scene(y)
        if feat is None:
            print(f"{y}: no scene"); continue
        nd = ndvi_array(feat)
        rows.append({"year": y, "date": feat["properties"]["datetime"][:10],
                     "cloud": round(feat["properties"]["eo:cloud_cover"], 1),
                     "mean_ndvi": round(float(np.nanmean(nd)), 4)})
        arrays[y] = nd
        print(f"{y}: {rows[-1]['date']} cloud={rows[-1]['cloud']:>4}  mean NDVI={rows[-1]['mean_ndvi']}")

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "greenness_argan.csv", index=False)

    # trend chart
    plt.style.use("seaborn-v0_8-whitegrid")
    z = np.polyfit(df["year"], df["mean_ndvi"], 1)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(df["year"], df["mean_ndvi"], marker="o", label="mean spring NDVI")
    ax.plot(df["year"], np.poly1d(z)(df["year"]), linestyle="--", color="black",
            label=f"trend: {z[0]*10:+.3f}/decade")
    ax.set_xlabel("Year")
    ax.set_ylabel("Mean spring NDVI")
    ax.set_title("Spring greenness (NDVI) of the argan slopes near Taroudant, 2017–2025")
    ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "fig_greenness_trend.png", dpi=150); plt.close(fig)
    print("wrote figures/fig_greenness_trend.png")

    # change map: wettest early year vs recent dry year, aligned grids
    y0 = min(arrays); y1 = 2024 if 2024 in arrays else max(arrays)
    a0, a1 = arrays[y0], arrays[y1]
    hh, ww = min(a0.shape[0], a1.shape[0]), min(a0.shape[1], a1.shape[1])
    diff = a1[:hh, :ww] - a0[:hh, :ww]
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(7, 7))
    im = ax.imshow(diff, cmap="BrBG", vmin=-0.3, vmax=0.3, interpolation="nearest")
    ax.set_title(f"Change in spring NDVI, {y0}–{y1}")
    ax.axis("off")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="NDVI change (brown = drier)")
    fig.tight_layout(); fig.savefig(FIG / "fig_greenness_change.png", dpi=150); plt.close(fig)
    print("wrote figures/fig_greenness_change.png")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()

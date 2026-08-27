"""
measure_souss_change.py
THE COST — how the irrigated footprint of the Souss plain changed, 2018 -> 2026.

The fourth panel of the "desert in disguise" story. National Geographic's
California lesson ends by asking students to design one more map for the part of
the story the first three do not tell. For the Souss, that part is the cost:
in a region that is drying, is the irrigated area shrinking (farms failing) or
growing (more water pumped from a falling aquifer)? Both answers are serious,
and the data decides which one is true.

Method: cloud-free spring Sentinel-2 NDVI composites for 2018 and 2026, both
reprojected onto one common lat/lon grid so the two years align exactly, then
differenced. Irrigated pixels are NDVI >= 0.35 (dense green in a semi-arid plain).

Outputs: data/geo/souss_ndvi_2018.tif, souss_ndvi_2026.tif, souss_change.tif,
         data/processed/souss_change.csv
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import numpy as np
import pandas as pd
import rasterio
import requests
from affine import Affine
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, transform as win_transform

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"
PROCESSED = ROOT / "data" / "processed"
STAC = "https://earth-search.aws.element84.com/v1/search"
AOI = (-9.60, 30.15, -8.55, 30.75)        # the Souss plain: Agadir -> Taroudant
RES = 0.0006                               # ~60 m common grid
SCL_BAD = {3, 8, 9, 10}
NDVI_IRRIGATED = 0.35
YEARS = (2018, 2026)


def scenes(year):
    r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-03-20T00:00:00Z/{year}-05-15T23:59:59Z",   # matched phenology window
        "query": {"eo:cloud_cover": {"lt": 15}}, "limit": 60}, timeout=60).json()
    f = r.get("features", [])
    f.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return f


def ndvi_on_grid(feat, dst_t, W, H):
    """NDVI for one scene, reprojected onto the common lat/lon grid."""
    red_h, nir_h, scl_h = (feat["assets"][b]["href"] for b in ("red", "nir", "scl"))
    with rasterio.open(red_h) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        if win.width < 10 or win.height < 10:
            return None
        sc = max(1, int(win.width // (W * 1.2)))
        oh, ow = max(1, int(win.height // sc)), max(1, int(win.width // sc))
        src_t = win_transform(win, src.transform) * Affine.scale(win.width / ow, win.height / oh)
        crs = src.crs

    def band(href):
        with rasterio.open(href) as s:
            return s.read(1, window=win, out_shape=(oh, ow)).astype("float32")

    red, nir, scl = band(red_h), band(nir_h), band(scl_h)
    valid = (red > 0) & (nir > 0) & ~np.isin(scl.astype(int), list(SCL_BAD))
    nd = np.where(nir + red > 0, (nir - red) / (nir + red + 1e-6), np.nan)
    nd[~valid] = np.nan

    out = np.full((H, W), np.nan, "float32")
    reproject(nd, out, src_transform=src_t, src_crs=crs, dst_transform=dst_t,
              dst_crs="EPSG:4326", src_nodata=np.nan, dst_nodata=np.nan,
              resampling=Resampling.bilinear)
    return out


def composite(year, dst_t, W, H, want=4):
    stack = []
    for feat in scenes(year)[:10]:
        try:
            nd = ndvi_on_grid(feat, dst_t, W, H)
        except Exception as e:
            print("   skip", feat["id"], str(e)[:60]); continue
        if nd is None:
            continue
        cov = float(np.isfinite(nd).mean())
        print(f"   {feat['id']}  cloud={feat['properties']['eo:cloud_cover']:.1f}  valid={cov:.2f}")
        if cov > 0.15:
            stack.append(nd)
        if len(stack) >= want:
            break
    if not stack:
        return None
    return np.nanmedian(np.dstack(stack), axis=2)


def main():
    GEO.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)
    print(f"common grid {W}x{H} @ ~{RES*111320:.0f} m")

    grids = {}
    for y in YEARS:
        print(f"\n{y}:")
        g = composite(y, dst_t, W, H)
        if g is None:
            print(f"  no usable scenes for {y}"); return
        grids[y] = g

    y0, y1 = YEARS
    a0, a1 = grids[y0], grids[y1]
    change = a1 - a0

    both = np.isfinite(a0) & np.isfinite(a1)
    # pixel area (m2) at this latitude
    px_km2 = (RES * 111.32) * (RES * 111.32 * np.cos(np.radians(30.45)))
    irr0 = (a0 >= NDVI_IRRIGATED) & both
    irr1 = (a1 >= NDVI_IRRIGATED) & both
    km2_0, km2_1 = irr0.sum() * px_km2, irr1.sum() * px_km2
    gained = (irr1 & ~irr0).sum() * px_km2
    lost = (irr0 & ~irr1).sum() * px_km2

    for arr, name in [(a0, f"souss_ndvi_{y0}.tif"), (a1, f"souss_ndvi_{y1}.tif"),
                      (change, "souss_change.tif")]:
        with rasterio.open(GEO / name, "w", driver="GTiff", height=H, width=W, count=1,
                           dtype="float32", crs="EPSG:4326", transform=dst_t,
                           nodata=np.nan, compress="deflate") as dst:
            dst.write(arr.astype("float32"), 1)
        print("wrote data/geo/" + name)

    pd.DataFrame([{"year_0": y0, "year_1": y1,
                   "irrigated_km2_y0": round(float(km2_0), 1),
                   "irrigated_km2_y1": round(float(km2_1), 1),
                   "change_km2": round(float(km2_1 - km2_0), 1),
                   "change_pct": round(100 * float(km2_1 - km2_0) / float(km2_0), 1) if km2_0 else None,
                   "gained_km2": round(float(gained), 1),
                   "lost_km2": round(float(lost), 1),
                   "mean_ndvi_change": round(float(np.nanmean(change)), 4)}]).to_csv(
        PROCESSED / "souss_change.csv", index=False)

    print(f"\nirrigated {y0}: {km2_0:,.0f} km2   ({km2_0*100:,.0f} ha)")
    print(f"irrigated {y1}: {km2_1:,.0f} km2   ({km2_1*100:,.0f} ha)")
    print(f"net change   : {km2_1-km2_0:+,.0f} km2  ({100*(km2_1-km2_0)/km2_0:+.1f}%)")
    print(f"  gained (new green): {gained:,.0f} km2")
    print(f"  lost (went brown) : {lost:,.0f} km2")
    print(f"mean NDVI change    : {np.nanmean(change):+.4f}")


if __name__ == "__main__":
    main()

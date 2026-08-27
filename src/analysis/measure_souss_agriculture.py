"""
measure_souss_agriculture.py
USE — the irrigated export-agriculture of the Souss plain.

The third panel of the "desert in disguise" story (after SUPPLY = rainfall and
DELIVERY = terrain/rivers): where the water actually goes. The Souss plain around
Agadir-Taroudant grows citrus and greenhouse vegetables for export in a semi-arid
rain shadow, irrigated largely from the Souss aquifer.

Method: a cloud-free spring Sentinel-2 composite over the plain; NDVI marks the
irrigated fields, which glow green against the surrounding brown desert. Pixels
above an NDVI threshold are counted as irrigated and the area is measured in UTM.

Outputs: data/geo/souss_ndvi.tif, data/geo/souss_irrigated.tif (0/1 mask),
         data/processed/souss_agriculture.csv
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
from rasterio.windows import from_bounds, transform as win_transform

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"
PROCESSED = ROOT / "data" / "processed"
STAC = "https://earth-search.aws.element84.com/v1/search"
AOI = (-9.60, 30.15, -8.55, 30.75)        # the Souss plain: Agadir -> Taroudant
TILE = "MGRS-29RNQ"
SCALE = 6                                  # ~60 m, regional view
SCL_BAD = {3, 8, 9, 10}
NDVI_IRRIGATED = 0.35                      # dense green in a semi-arid plain


def candidate_scenes(year=2026):
    r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-02-01T00:00:00Z/{year}-05-15T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 15}}, "limit": 60}, timeout=60).json()
    feats = r.get("features", [])
    feats.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return feats


def read_band(href, win, out_shape):
    with rasterio.open(href) as src:
        return src.read(1, window=win, out_shape=out_shape).astype("float32")


def ndvi_for(feat):
    red_h, nir_h, scl_h = (feat["assets"][b]["href"] for b in ("red", "nir", "scl"))
    with rasterio.open(red_h) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (max(1, int(win.height // SCALE)), max(1, int(win.width // SCALE)))
        base_t = win_transform(win, src.transform) * Affine.scale(SCALE, SCALE)
        crs = src.crs
    red = read_band(red_h, win, out_shape)
    nir = read_band(nir_h, win, out_shape)
    scl = read_band(scl_h, win, out_shape)
    valid = (red > 0) & (nir > 0) & ~np.isin(scl.astype(int), list(SCL_BAD))
    ndvi = np.where(nir + red > 0, (nir - red) / (nir + red + 1e-6), np.nan)
    ndvi[~valid] = np.nan
    return ndvi, base_t, crs


def main():
    GEO.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    stack, tr, crs = [], None, None
    for feat in candidate_scenes()[:8]:
        try:
            nd, t, c = ndvi_for(feat)
        except Exception as e:
            print("  skip", feat["id"], e); continue
        cov = float(np.isfinite(nd).mean())
        print(f"  {feat['id']}  cloud={feat['properties']['eo:cloud_cover']:.1f}  valid={cov:.2f}")
        if cov < 0.1:
            continue
        if tr is None:
            tr, crs = t, c
            stack.append(nd)
        elif nd.shape == stack[0].shape:
            stack.append(nd)
        if len(stack) >= 4:
            break
    if not stack:
        print("no usable scenes"); return

    ndvi = np.nanmedian(np.dstack(stack), axis=2)      # cloud-robust composite
    print("composite from", len(stack), "scenes, shape", ndvi.shape)

    irrigated = (ndvi >= NDVI_IRRIGATED).astype("uint8")
    irrigated[~np.isfinite(ndvi)] = 0

    # pixel area in UTM metres
    px_m = abs(tr.a) * abs(tr.e)
    area_km2 = float(irrigated.sum()) * px_m / 1e6
    total_km2 = float(np.isfinite(ndvi).sum()) * px_m / 1e6

    for arr, name, dt in [(ndvi.astype("float32"), "souss_ndvi.tif", "float32"),
                          (irrigated, "souss_irrigated.tif", "uint8")]:
        with rasterio.open(GEO / name, "w", driver="GTiff", height=arr.shape[0],
                           width=arr.shape[1], count=1, dtype=dt, crs=crs, transform=tr,
                           nodata=(np.nan if dt == "float32" else 0), compress="deflate") as dst:
            dst.write(arr, 1)
        print("wrote data/geo/" + name)

    pd.DataFrame([{"irrigated_km2": round(area_km2, 1),
                   "scene_km2": round(total_km2, 1),
                   "irrigated_pct": round(100 * area_km2 / total_km2, 1),
                   "ndvi_threshold": NDVI_IRRIGATED,
                   "scenes_used": len(stack)}]).to_csv(
        PROCESSED / "souss_agriculture.csv", index=False)

    print(f"\nirrigated / dense vegetation: {area_km2:,.0f} km2 "
          f"({100*area_km2/total_km2:.1f}% of the plain scene)")
    print(f"  = {area_km2*100:,.0f} hectares of green in a rain-shadow desert")


if __name__ == "__main__":
    main()

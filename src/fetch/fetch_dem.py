"""
fetch_dem.py
Build a small terrain DEM of the Oum Er-Rbia area from the open Copernicus GLO-30
digital elevation model (public, no account). Used for the shaded-relief +
hypsometric-tint "water journey" map.

Reads each 1-degree COG tile decimated (from its overviews, so it's fast and
light, not a full download) and mosaics onto a regular ~90 m grid.
Output: data/dem/oer_dem.tif  (gitignored; regenerate by rerunning this).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from affine import Affine
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "dem" / "oer_dem.tif"
BASE = "https://copernicus-dem-30m.s3.amazonaws.com"

# 1-degree tiles (lower-left corner) covering lon [-8,-6], lat [32,34]
TILES = [(32, 8), (32, 7), (33, 8), (33, 7)]
DECIMATE = 3            # ~30 m -> ~90 m read from overviews
RES = 0.0009           # output grid ~100 m
BBOX = (-8.0, 32.0, -6.0, 34.0)


def tile_url(lat: int, lon: int) -> str:
    name = f"Copernicus_DSM_COG_10_N{lat:02d}_00_W{lon:03d}_00_DEM"
    return f"{BASE}/{name}/{name}.tif"


def main() -> None:
    w = int(round((BBOX[2] - BBOX[0]) / RES))
    h = int(round((BBOX[3] - BBOX[1]) / RES))
    dst_transform = from_origin(BBOX[0], BBOX[3], RES, RES)
    union = np.full((h, w), np.nan, dtype="float32")

    for lat, lon in TILES:
        with rasterio.open(tile_url(lat, lon)) as src:
            oh, ow = src.height // DECIMATE, src.width // DECIMATE
            arr = src.read(1, out_shape=(oh, ow),
                           resampling=Resampling.bilinear).astype("float32")
            s_transform = src.transform * Affine.scale(src.width / ow, src.height / oh)
            tmp = np.full((h, w), np.nan, dtype="float32")
            reproject(arr, tmp, src_transform=s_transform, src_crs=src.crs,
                      dst_transform=dst_transform, dst_crs="EPSG:4326",
                      src_nodata=src.nodata, dst_nodata=np.nan,
                      resampling=Resampling.bilinear)
            union = np.where(np.isnan(union), tmp, union)
        print(f"mosaicked tile N{lat} W{lon:03d}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prof = dict(driver="GTiff", height=h, width=w, count=1, dtype="float32",
                crs="EPSG:4326", transform=dst_transform, nodata=np.nan,
                compress="deflate", tiled=True)
    with rasterio.open(OUT, "w", **prof) as dst:
        dst.write(union, 1)
    print(f"wrote {OUT.relative_to(ROOT)}  {union.shape}  "
          f"elev {np.nanmin(union):.0f}-{np.nanmax(union):.0f} m")


if __name__ == "__main__":
    main()

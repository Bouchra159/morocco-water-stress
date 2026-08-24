"""
fetch_souss_dem.py
Copernicus GLO-30 DEM mosaic for the whole Souss-Massa region (the author's home
region), decimated to a manageable grid for regional cartography.

Public AWS bucket, no login. Outputs data/dem/souss_massa_dem.tif (EPSG:4326).
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "dem" / "souss_massa_dem.tif"
BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
AOI = (-10.0, 28.3, -6.35, 31.2)          # Souss-Massa region bbox
RES = 0.0025                               # ~275 m, good for a regional map


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)
    mosaic = np.full((H, W), np.nan, "float32")
    print(f"target grid {W}x{H}")

    for lat in range(int(AOI[1]), int(AOI[3]) + 1):
        for lon in range(int(AOI[0]) - 1, int(AOI[2]) + 1):
            name = f"Copernicus_DSM_COG_10_N{lat:02d}_00_W{abs(lon):03d}_00_DEM"
            url = f"{BASE}/{name}/{name}.tif"
            try:
                with rasterio.open(url) as src:
                    arr = src.read(1, out_shape=(src.height // 4, src.width // 4)).astype("float32")
                    src_t = src.transform * rasterio.Affine.scale(4, 4)
                    tmp = np.full((H, W), np.nan, "float32")
                    reproject(arr, tmp, src_transform=src_t, src_crs=src.crs,
                              dst_transform=dst_t, dst_crs="EPSG:4326",
                              src_nodata=src.nodata, dst_nodata=np.nan,
                              resampling=Resampling.bilinear)
                    m = np.isfinite(tmp)
                    mosaic[m] = tmp[m]
                    print("  +", name)
            except Exception:
                pass            # tile does not exist (ocean) - fine

    mosaic = np.nan_to_num(mosaic, nan=0.0)
    with rasterio.open(OUT, "w", driver="GTiff", height=H, width=W, count=1,
                       dtype="float32", crs="EPSG:4326", transform=dst_t,
                       compress="deflate") as dst:
        dst.write(mosaic, 1)
    print(f"wrote {OUT}  min={mosaic.min():.0f} max={mosaic.max():.0f} m")


if __name__ == "__main__":
    main()

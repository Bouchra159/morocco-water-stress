"""
build_greenness_map.py
A proper cartographic GIS deliverable: a map of vegetation change (NDVI difference,
2018 -> 2024) on the argan / Anti-Atlas slopes near Taroudant, draped over a
hillshade of the terrain.

This is a real multi-source GIS workflow:
  - Sentinel-2 spring NDVI for two years (remote sensing)
  - reprojected from UTM onto a common lat/lon grid (rasterio.warp)
  - differenced to a change raster, saved as a GeoTIFF (GIS output)
  - overlaid on a Copernicus-DEM hillshade with map furniture (scale bar,
    north arrow, coordinate ticks, legend, place labels)

Run src/measure_greenness.py at least once is not required; this is self-contained.
Outputs: data/geo/ndvi_change_argan.tif, figures/map_greenness_change.png
"""
from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from affine import Affine
from matplotlib.colors import LightSource
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, transform as win_transform

import build_home_map as home        # for the DEM + fetch_dem()
import measure_greenness as mg       # AOI, tile, scene search, bands

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"
FIG = ROOT / "figures"

AOI = mg.AOI                          # (-8.65, 30.05, -8.35, 30.35)
RES = 0.0003                          # ~33 m grid, lat/lon
Y0, Y1 = 2018, 2026


def ndvi_on_grid(year: int, dst_transform, W: int, H: int) -> np.ndarray:
    feat = mg.best_spring_scene(year)
    red_h, nir_h, scl_h = (feat["assets"][b]["href"] for b in ("red", "nir", "scl"))
    with rasterio.open(red_h) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        sc = 3
        oh, ow = int(win.height // sc), int(win.width // sc)
        src_t = win_transform(win, src.transform) * Affine.scale(sc, sc)
        src_crs = src.crs
    red = mg.read_band(red_h, win, (oh, ow))
    nir = mg.read_band(nir_h, win, (oh, ow))
    scl = mg.read_band(scl_h, win, (oh, ow))
    valid = (red > 0) & (nir > 0) & ~np.isin(scl.astype(int), list(mg.SCL_BAD))
    nd = np.where(red + nir > 0, (nir - red) / (nir + red + 1e-6), np.nan)
    nd[~valid] = np.nan
    dst = np.full((H, W), np.nan, "float32")
    reproject(nd, dst, src_transform=src_t, src_crs=src_crs,
              dst_transform=dst_transform, dst_crs="EPSG:4326",
              src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.bilinear)
    print(f"{year}: NDVI gridded")
    return dst


def dem_on_grid(dst_transform, W: int, H: int) -> np.ndarray:
    home.fetch_dem()                  # ensures data/dem/souss_dem.tif exists
    dst = np.full((H, W), np.nan, "float32")
    with rasterio.open(home.DEM) as src:
        reproject(rasterio.band(src, 1), dst, dst_transform=dst_transform,
                  dst_crs="EPSG:4326", dst_nodata=np.nan, resampling=Resampling.bilinear)
    return dst


def scale_bar(ax, lon0, lat0, km=10):
    deg = km / (111.32 * np.cos(np.radians(lat0)))   # km -> degrees lon at this lat
    ax.plot([lon0, lon0 + deg], [lat0, lat0], color="black", lw=3, solid_capstyle="butt")
    ax.text(lon0 + deg / 2, lat0 + 0.006, f"{km} km", ha="center", fontsize=9)


def main() -> None:
    GEO.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)

    nd0 = ndvi_on_grid(Y0, dst_t, W, H)
    nd1 = ndvi_on_grid(Y1, dst_t, W, H)
    change = nd1 - nd0
    dem = dem_on_grid(dst_t, W, H)

    # save the change raster as a real GIS output
    with rasterio.open(GEO / "ndvi_change_argan.tif", "w", driver="GTiff",
                       height=H, width=W, count=1, dtype="float32", crs="EPSG:4326",
                       transform=dst_t, nodata=np.nan, compress="deflate") as dst:
        dst.write(change, 1)
    print("wrote data/geo/ndvi_change_argan.tif")

    ls = LightSource(azdeg=315, altdeg=45)
    hs = ls.hillshade(np.nan_to_num(dem), vert_exag=3, dx=33, dy=33)
    extent = (AOI[0], AOI[2], AOI[1], AOI[3])

    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(9.5, 8.6))
    ax.imshow(hs, cmap="gray", extent=extent, origin="upper")
    im = ax.imshow(change, cmap="BrBG", vmin=-0.25, vmax=0.25, extent=extent,
                   origin="upper", alpha=0.72)

    # place label (Igherm sits inside the AOI)
    ax.plot(-8.47, 30.09, "o", color="black", ms=6, markeredgecolor="white")
    ax.annotate("Igherm", (-8.47, 30.09), xytext=(6, 4),
                textcoords="offset points", fontsize=10, fontweight="bold")

    # map furniture
    ax.annotate("N", xy=(AOI[0] + 0.02, AOI[3] - 0.02), fontsize=13, fontweight="bold", ha="center")
    ax.annotate("", xy=(AOI[0] + 0.02, AOI[3] - 0.008), xytext=(AOI[0] + 0.02, AOI[3] - 0.045),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.6))
    scale_bar(ax, AOI[0] + 0.02, AOI[1] + 0.02, km=5)

    ax.set_xlim(AOI[0], AOI[2]); ax.set_ylim(AOI[1], AOI[3])
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title(f"Vegetation change on the argan slopes near Taroudant, spring {Y0}–{Y1}\n"
                 "Sentinel-2 NDVI difference over a Copernicus-DEM hillshade")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
    cbar.set_label("NDVI change  (brown = browner / drier,  green = greener)")
    fig.tight_layout()
    fig.savefig(FIG / "map_greenness_change.png", dpi=180)
    plt.close(fig)
    print("wrote figures/map_greenness_change.png")


if __name__ == "__main__":
    main()

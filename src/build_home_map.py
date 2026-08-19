"""
build_home_map.py
"Argan Country" — a shaded-relief map of the author's home region: the Souss valley
and the Anti-Atlas of southern Morocco (Taroudant / Souss-Massa), the argan belt.

This is the personal heart of the project: Al Massira (elsewhere in this repo) is
where I proved the method; this is the land I come from, and why the whole thing
exists. Self-contained — fetches its own Copernicus DEM tiles, then renders in
pure Python (matplotlib hillshade). Output: figures/map_argan_country.png

Run: python src/build_home_map.py
"""
from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from affine import Affine
from matplotlib.colors import LightSource, LinearSegmentedColormap, Normalize
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling

ROOT = Path(__file__).resolve().parents[1]
DEM = ROOT / "data" / "dem" / "souss_dem.tif"
FIG = ROOT / "figures"
BASE = "https://copernicus-dem-30m.s3.amazonaws.com"

TILES = [(30, 9), (30, 10), (31, 9), (31, 10)]   # lon [-10,-8], lat [30,32]
DEC, RES = 3, 0.0009
BBOX = (-10.0, 30.0, -8.0, 32.0)

INK = "#241c14"
_STOPS = [(0.00, "#d8c9a0"), (0.10, "#dcc892"), (0.22, "#d8bc80"), (0.32, "#cda869"),
          (0.45, "#bf925a"), (0.60, "#a97a4a"), (0.72, "#9a6c44"), (0.82, "#95806e"),
          (0.92, "#c9bdae"), (1.00, "#f4f0ea")]
HYPSO = LinearSegmentedColormap.from_list("arid", _STOPS)
TOWNS = {"Agadir": (-9.58, 30.42), "Taroudant": (-8.88, 30.47),
         "Oulad Teima": (-9.21, 30.39), "Aoulouz": (-8.16, 30.68),
         "Igherm": (-8.47, 30.09), "Ait Baha": (-9.15, 30.07)}
EXTENT_LL = (-9.9, -8.1, 30.0, 31.15)


def fetch_dem() -> None:
    if DEM.exists():
        return
    w = int(round((BBOX[2] - BBOX[0]) / RES))
    h = int(round((BBOX[3] - BBOX[1]) / RES))
    dst_t = from_origin(BBOX[0], BBOX[3], RES, RES)
    union = np.full((h, w), np.nan, dtype="float32")
    for lat, lon in TILES:
        name = f"Copernicus_DSM_COG_10_N{lat:02d}_00_W{lon:03d}_00_DEM"
        with rasterio.open(f"{BASE}/{name}/{name}.tif") as src:
            oh, ow = src.height // DEC, src.width // DEC
            arr = src.read(1, out_shape=(oh, ow), resampling=Resampling.bilinear).astype("float32")
            s_t = src.transform * Affine.scale(src.width / ow, src.height / oh)
            tmp = np.full((h, w), np.nan, dtype="float32")
            reproject(arr, tmp, src_transform=s_t, src_crs=src.crs, dst_transform=dst_t,
                      dst_crs="EPSG:4326", src_nodata=src.nodata, dst_nodata=np.nan,
                      resampling=Resampling.bilinear)
            union = np.where(np.isnan(union), tmp, union)
        print(f"mosaicked N{lat} W{lon:03d}")
    DEM.parent.mkdir(parents=True, exist_ok=True)
    prof = dict(driver="GTiff", height=h, width=w, count=1, dtype="float32",
                crs="EPSG:4326", transform=dst_t, nodata=np.nan, compress="deflate", tiled=True)
    with rasterio.open(DEM, "w", **prof) as dst:
        dst.write(union, 1)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    fetch_dem()
    with rasterio.open(DEM) as src:
        dem = np.nan_to_num(src.read(1).astype("float32"), nan=0.0)
        b = src.bounds
        full = (b.left, b.right, b.bottom, b.top)

    ls = LightSource(azdeg=315, altdeg=45)
    rgb = ls.shade(dem, cmap=HYPSO, norm=Normalize(0, 3580),
                   blend_mode="soft", vert_exag=3, dx=90, dy=90)

    fig, ax = plt.subplots(figsize=(12, 8.4))
    ax.imshow(rgb, extent=full, origin="upper")
    ax.set_xlim(EXTENT_LL[0], EXTENT_LL[1])
    ax.set_ylim(EXTENT_LL[2], EXTENT_LL[3])
    for name, (lon, lat) in TOWNS.items():
        big = name in ("Agadir", "Taroudant")
        ax.plot(lon, lat, "o", ms=8 if big else 5, color=INK,
                markeredgecolor="white", markeredgewidth=1.1, zorder=5)
        ax.annotate(name, (lon, lat), textcoords="offset points", xytext=(7, 3),
                    fontsize=12 if big else 10, fontweight="bold" if big else "normal",
                    color=INK, zorder=6)

    def land(txt, lon, lat, size):
        ax.text(lon, lat, txt, fontsize=size, color="#4a3016", alpha=0.75, ha="center",
                va="center", fontweight="bold", style="italic", zorder=4)
    land("H I G H   A T L A S", -8.7, 31.0, 15)
    land("S O U S S   V A L L E Y", -9.0, 30.42, 12)
    land("A N T I - A T L A S", -8.7, 30.15, 15)

    ax.set_title("Argan Country — the Souss valley and the Anti-Atlas",
                 fontsize=17, fontweight="bold", color="#5a3a1c", loc="left", pad=12)
    ax.text(0.0, 1.008, "Home ground: a dry land between two mountain ranges, where the argan tree holds on",
            transform=ax.transAxes, fontsize=12, color="#4a3320")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor("#333333")
    fig.text(0.125, 0.045, "Terrain: Copernicus GLO-30 DEM (ESA / Copernicus). Shaded relief + "
             "hypsometric tint. Cartography: B. Daddaoui, 2026.", fontsize=8.5, color="#7a6f5f")
    fig.savefig(FIG / "map_argan_country.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote figures/map_argan_country.png")


if __name__ == "__main__":
    main()

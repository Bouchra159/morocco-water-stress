"""
classify_landcover.py
Unsupervised land-cover classification of the Souss / argan area near Taroudant
from Sentinel-2 — a standard remote-sensing analyst workflow.

Method: read six surface-reflectance bands + three indices (NDVI, NDWI, NDBI),
mask cloud, standardise, and cluster with K-means (unsupervised). Clusters are
then labelled by their spectral signatures (NDWI for water, NDVI for vegetation
density, brightness/SWIR for bare ground). Honest note: this is an *unsupervised*
classification with spectrally-interpreted labels, not a ground-truthed map.

Outputs: data/geo/landcover_souss.tif (classified GeoTIFF, EPSG:4326),
         figures/map_landcover.png
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import matplotlib.pyplot as plt
import numpy as np
import rasterio
import requests
from affine import Affine
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, transform as win_transform
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"
FIG = ROOT / "figures"
STAC = "https://earth-search.aws.element84.com/v1/search"
TILE = "MGRS-29RNP"
AOI = (-8.62, 30.15, -8.28, 30.52)
RES = 0.0004          # ~40 m output grid
N_CLUSTERS = 6
SCL_BAD = {3, 8, 9, 10}


def best_scene():
    r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": "2026-03-01T00:00:00Z/2026-05-31T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 8}, "grid:code": {"eq": TILE}}, "limit": 40},
        timeout=40).json()
    feats = [f for f in r["features"] if f["properties"].get("grid:code") == TILE]
    feats.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return feats[0]


def read_to_grid(href, dst_t, W, H):
    with rasterio.open(href) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        sc = max(1, int(win.width // (W * 1.2)))
        oh, ow = int(win.height // sc), int(win.width // sc)
        arr = src.read(1, window=win, out_shape=(oh, ow)).astype("float32")
        src_t = win_transform(win, src.transform) * Affine.scale(win.width / ow, win.height / oh)
        crs = src.crs
    out = np.full((H, W), np.nan, "float32")
    reproject(arr, out, src_transform=src_t, src_crs=crs, dst_transform=dst_t,
              dst_crs="EPSG:4326", src_nodata=0, dst_nodata=np.nan, resampling=Resampling.bilinear)
    return out


def main():
    GEO.mkdir(parents=True, exist_ok=True); FIG.mkdir(exist_ok=True)
    feat = best_scene()
    print("scene:", feat["id"], "cloud", feat["properties"]["eo:cloud_cover"])
    W = int(round((AOI[2] - AOI[0]) / RES)); H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)

    a = feat["assets"]
    bands = {b: read_to_grid(a[b]["href"], dst_t, W, H)
             for b in ("blue", "green", "red", "nir", "swir16", "swir22")}
    scl = read_to_grid(a["scl"]["href"], dst_t, W, H)

    ndvi = (bands["nir"] - bands["red"]) / (bands["nir"] + bands["red"] + 1e-6)
    ndwi = (bands["green"] - bands["nir"]) / (bands["green"] + bands["nir"] + 1e-6)
    ndbi = (bands["swir16"] - bands["nir"]) / (bands["swir16"] + bands["nir"] + 1e-6)
    feats = np.dstack([bands[b] for b in bands] + [ndvi * 10000, ndwi * 10000, ndbi * 10000])

    scl_int = np.where(np.isfinite(scl), scl, -1).astype(int)
    valid = np.isfinite(feats).all(axis=2) & ~np.isin(scl_int, list(SCL_BAD))
    X = feats[valid]
    Xs = StandardScaler().fit_transform(X)
    km = MiniBatchKMeans(n_clusters=N_CLUSTERS, random_state=0, n_init=10).fit(Xs)

    labels = np.full((H, W), -1, "int16")
    labels[valid] = km.labels_

    # label clusters by spectral signature
    stats = []
    for k in range(N_CLUSTERS):
        m = labels == k
        stats.append({"k": k, "ndvi": np.nanmean(ndvi[m]), "ndwi": np.nanmean(ndwi[m]),
                      "bright": np.nanmean((bands["red"] + bands["green"] + bands["blue"])[m])})
    water_k = max(stats, key=lambda s: s["ndwi"])
    names, used = {}, set()
    if water_k["ndwi"] > 0.0:
        names[water_k["k"]] = "Water"; used.add(water_k["k"])
    rest = sorted([s for s in stats if s["k"] not in used], key=lambda s: -s["ndvi"])
    veg_labels = ["Irrigated / dense vegetation", "Argan woodland / shrub",
                  "Sparse vegetation", "Bare soil", "Rock / mountain", "Other / mixed"]
    for s, lab in zip(rest, veg_labels):
        names[s["k"]] = lab
    order = ([water_k["k"]] if water_k["k"] in used else []) + [s["k"] for s in rest]
    palette = {"Water": "#2a6f97", "Irrigated / dense vegetation": "#1a7a3a",
               "Argan woodland / shrub": "#7ba05a", "Sparse vegetation": "#cdd89a",
               "Bare soil": "#d9b98a", "Rock / mountain": "#9a8a7a", "Other / mixed": "#b0a090"}

    # build a display raster in the class order
    remap = {k: i for i, k in enumerate(order)}
    disp = np.full((H, W), np.nan)
    for k, i in remap.items():
        disp[labels == k] = i
    colors = [palette[names[k]] for k in order]
    cmap = ListedColormap(colors)

    # save classified GeoTIFF (0..N classes, 255 = nodata)
    class_raster = np.full((H, W), 255, "uint8")
    for k, i in remap.items():
        class_raster[labels == k] = i
    with rasterio.open(GEO / "landcover_souss.tif", "w", driver="GTiff", height=H, width=W,
                       count=1, dtype="uint8", crs="EPSG:4326", transform=dst_t, nodata=255,
                       compress="deflate") as dst:
        dst.write(class_raster, 1)
    print("wrote data/geo/landcover_souss.tif")

    px_km2 = (RES * 111.32) * (RES * 111.32 * np.cos(np.radians(30.35)))
    plt.style.use("default")
    fig, ax = plt.subplots(figsize=(9.5, 8.6))
    ax.imshow(disp, cmap=cmap, extent=(AOI[0], AOI[2], AOI[1], AOI[3]), origin="upper",
              vmin=-0.5, vmax=len(order) - 0.5)
    legend = [Patch(facecolor=palette[names[k]],
                    label=f"{names[k]}  ({(labels == k).sum() * px_km2:.0f} km²)") for k in order]
    ax.legend(handles=legend, loc="lower left", fontsize=9, framealpha=0.9)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("Land-cover classification near Taroudant (Souss / argan area)\n"
                 "Unsupervised K-means on Sentinel-2, spring 2026")
    fig.tight_layout(); fig.savefig(FIG / "map_landcover.png", dpi=180); plt.close(fig)
    print("wrote figures/map_landcover.png")


if __name__ == "__main__":
    main()

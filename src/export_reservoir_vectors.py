"""
export_reservoir_vectors.py
Vectorise the Sentinel-2 water masks into polygons for high-quality mapping.

Re-measures selected years at full 10 m resolution, polygonises the NDWI+Otsu
water mask, and writes a GeoPackage (EPSG:4326) with one water polygon per year.
This is what the QGIS print layout (src/qgis_reservoir_layout.py) styles.

Output: data/geo/al_massira_water.gpkg  (layer 'water', field 'year')
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
import rasterio.features
from affine import Affine
from pyproj import Transformer
from rasterio.windows import from_bounds, transform as win_transform
from shapely.geometry import shape

import measure_reservoir as mr  # same folder

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"

HERO_YEARS = [2017, 2024]   # full pool vs collapse
FULL_SCALE = 1              # 10 m — crisp outlines for print
MIN_POLY_PX = 50            # drop speckle smaller than this many pixels


def water_polygons(feat, scale=FULL_SCALE):
    green_href = feat["assets"]["green"]["href"]
    nir_href = feat["assets"]["nir"]["href"]
    scl_href = feat["assets"]["scl"]["href"]

    with rasterio.open(green_href) as src:
        crs = src.crs
        tf = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        xmin, ymin = tf.transform(mr.AOI[0], mr.AOI[1])
        xmax, ymax = tf.transform(mr.AOI[2], mr.AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        out_shape = (int(win.height // scale), int(win.width // scale))
        base_tf = win_transform(win, src.transform)
        out_tf = base_tf * Affine.scale(scale, scale)

    green = mr.read_band(green_href, win, out_shape)
    nir = mr.read_band(nir_href, win, out_shape)
    scl = mr.read_band(scl_href, win, out_shape)

    valid = (green > 0) & (nir > 0) & ~np.isin(scl.astype(int), list(mr.SCL_BAD))
    ndwi = np.where(green + nir > 0, (green - nir) / (green + nir + 1e-6), np.nan)
    thr = max(mr.otsu(ndwi[valid]), 0.0)
    water = ((ndwi > thr) & valid).astype("uint8")

    geoms = []
    for geom, val in rasterio.features.shapes(water, mask=water == 1, transform=out_tf):
        if val == 1:
            geoms.append(shape(geom))
    gdf = gpd.GeoDataFrame(geometry=geoms, crs=crs)
    # drop speckle, keep meaningful water bodies
    px_area = (10 * scale) ** 2
    gdf = gdf[gdf.geometry.area >= MIN_POLY_PX * px_area]
    # dissolve to a single multipolygon for the year
    dissolved = gdf.dissolve().to_crs("EPSG:4326")
    return dissolved.geometry.iloc[0]


def main():
    GEO.mkdir(parents=True, exist_ok=True)
    records = []
    for y in HERO_YEARS:
        feat = mr.best_scene(y)
        if feat is None:
            print(f"{y}: no scene")
            continue
        geom = water_polygons(feat)
        area = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:32629").area.iloc[0] / 1e6
        records.append({"year": y, "date": feat["properties"]["datetime"][:10],
                        "area_km2": round(float(area), 1), "geometry": geom})
        print(f"{y}: water polygon area = {area:.1f} km2")

    out = GEO / "al_massira_water.gpkg"
    gpd.GeoDataFrame(records, crs="EPSG:4326").to_file(out, layer="water", driver="GPKG")
    print("wrote", out.relative_to(ROOT))


if __name__ == "__main__":
    main()

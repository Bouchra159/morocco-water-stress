"""
pipeline_spatial_sql.py
Spatial SQL + cloud-native vector pipeline.

Modern spatial data science happens in a database, not in a pile of files. This
runs real spatial SQL over the project's geodatabase using DuckDB with its
spatial extension - server-free, but the same ST_* functions you would write
against PostGIS - and publishes the result as GeoParquet, the cloud-native
vector format that replaces the shapefile.

What it answers (a real downstream-vulnerability question):
    Al Massira lost 91% of its surface between 2017 and 2024. Which communities
    sit closest to that water, how far did the shoreline retreat from them, and
    which irrigated farmland is exposed?

Pipeline
  1. vectorise the Doukkala irrigated cropland raster into field polygons
  2. load every vector layer into DuckDB (spatial extension)
  3. run spatial SQL: ST_Area / ST_Distance / ST_DWithin / ST_Intersects,
     always measuring in UTM 29N (EPSG:32629) - never in degrees
  4. validate the SQL-computed reservoir areas against the independently
     measured satellite numbers (98 / 9 km2)

CRS GOTCHA WORTH KNOWING
    DuckDB's ST_Transform honours the OFFICIAL EPSG:4326 axis order, which is
    (latitude, longitude) - not the (longitude, latitude) that GeoJSON, shapely
    and geopandas use. Without `always_xy := true` it silently swaps the
    coordinates and every area and distance comes out wrong: the 2017 reservoir
    measured 204.5 km2 instead of 98.8 km2, a 2x error with no warning. This was
    caught only by validating the SQL against an independent measurement.
  5. export GeoParquet + CSV

Outputs: data/geo/parquet/*.parquet   (GeoParquet, cloud-native vector)
         data/processed/spatial_sql_report.csv
"""
from __future__ import annotations

from pathlib import Path

import duckdb
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import shapes
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
GPKG = ROOT / "gis" / "morocco_water.gpkg"
GEO = ROOT / "data" / "geo"
PARQUET = GEO / "parquet"
PROCESSED = ROOT / "data" / "processed"

UTM = 32629                      # UTM 29N - the metric CRS for western Morocco
NDMI_CROP = 0.10                 # moist vegetation = actively irrigated field
MIN_FIELD_KM2 = 0.05             # drop specks smaller than 5 ha


def vectorise_cropland() -> gpd.GeoDataFrame | None:
    """Turn the Doukkala crop-moisture raster into irrigated-field polygons."""
    src_path = GEO / "crop_ndmi_2026.tif"
    if not src_path.exists():
        print("  crop raster missing - skipping cropland vectorisation")
        return None
    with rasterio.open(src_path) as src:
        arr = src.read(1)
        mask = np.isfinite(arr) & (arr >= NDMI_CROP)
        polys = [shape(g) for g, v in shapes(mask.astype("uint8"), mask=mask,
                                             transform=src.transform) if v == 1]
        crs = src.crs
    if not polys:
        return None
    gdf = gpd.GeoDataFrame({"field_id": range(1, len(polys) + 1)},
                           geometry=polys, crs=crs).to_crs(4326)
    gdf["area_km2"] = gdf.to_crs(UTM).area / 1e6
    gdf = gdf[gdf["area_km2"] >= MIN_FIELD_KM2].reset_index(drop=True)
    gdf["field_id"] = range(1, len(gdf) + 1)
    print(f"  vectorised {len(gdf):,} irrigated field polygons "
          f"({gdf['area_km2'].sum():,.0f} km2)")
    return gdf


def main() -> None:
    PARQUET.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    print("initialising DuckDB spatial ...")
    con = duckdb.connect(database=":memory:")
    con.execute("INSTALL spatial; LOAD spatial;")

    # ---- 1. load the geodatabase ------------------------------------------
    layers = {}
    for name in ("reservoirs", "dams", "communities"):
        try:
            layers[name] = gpd.read_file(GPKG, layer=name).to_crs(4326)
            print(f"  loaded {name:12s} {len(layers[name]):>4} features")
        except Exception as e:
            print(f"  could not load {name}: {e}")

    fields = vectorise_cropland()
    if fields is not None:
        layers["fields"] = fields

    # register each layer in DuckDB as WKT -> geometry
    for name, gdf in layers.items():
        df = pd.DataFrame(gdf.drop(columns=gdf.geometry.name))
        df["wkt"] = gdf.geometry.to_wkt()
        con.register(f"{name}_df", df)
        con.execute(f"CREATE TABLE {name} AS "
                    f"SELECT * EXCLUDE (wkt), ST_GeomFromText(wkt) AS geom FROM {name}_df")
    print(f"\nloaded {len(layers)} tables into DuckDB\n")

    reports: list[pd.DataFrame] = []

    # ---- 2. reservoir area in UTM, validated against the satellite numbers --
    if "reservoirs" in layers:
        q = f"""
        SELECT year,
               ROUND(SUM(ST_Area(ST_Transform(geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true))) / 1e6, 1)
                   AS area_km2_sql
        FROM reservoirs
        GROUP BY year
        ORDER BY year
        """
        area = con.execute(q).df()
        print("RESERVOIR AREA computed in spatial SQL (measured in UTM, not degrees)")
        print(area.to_string(index=False))
        print("  cross-check: satellite measurement gave 98 km2 (2017) and 9 km2 (2024)\n")
        area.to_csv(PROCESSED / "sql_reservoir_area.csv", index=False)

    # ---- 3. how far is each community from the water, 2017 vs 2024? --------
    if {"communities", "reservoirs"} <= set(layers):
        q = f"""
        WITH c AS (SELECT name, population_2014,
                          ST_Transform(geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true) AS g
                   FROM communities),
             r AS (SELECT year,
                          ST_Transform(ST_Union_Agg(geom), 'EPSG:4326', 'EPSG:{UTM}', always_xy := true) AS g
                   FROM reservoirs GROUP BY year)
        SELECT c.name,
               c.population_2014,
               ROUND(MIN(CASE WHEN r.year = 2017 THEN ST_Distance(c.g, r.g) END) / 1000, 1)
                   AS km_to_water_2017,
               ROUND(MIN(CASE WHEN r.year = 2024 THEN ST_Distance(c.g, r.g) END) / 1000, 1)
                   AS km_to_water_2024
        FROM c CROSS JOIN r
        GROUP BY c.name, c.population_2014
        ORDER BY km_to_water_2024
        """
        try:
            d = con.execute(q).df()
            d["shoreline_retreat_km"] = (d["km_to_water_2024"] - d["km_to_water_2017"]).round(1)
            print("HOW FAR THE WATER MOVED AWAY FROM EACH COMMUNITY")
            print(d.to_string(index=False))
            print()
            d.to_csv(PROCESSED / "sql_community_distance.csv", index=False)
            reports.append(d)
        except Exception as e:
            print("  community-distance query failed:", e)

    # ---- 4. ST_DWithin: which communities are within 25 km of 2024 water? --
    if {"communities", "reservoirs"} <= set(layers):
        q = f"""
        SELECT c.name, c.population_2014
        FROM communities c, reservoirs r
        WHERE r.year = 2024
          AND ST_DWithin(ST_Transform(c.geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true),
                         ST_Transform(r.geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true), 25000)
        GROUP BY c.name, c.population_2014
        ORDER BY c.population_2014 DESC
        """
        try:
            near = con.execute(q).df()
            print(f"ST_DWithin - communities within 25 km of the 2024 shoreline: {len(near)}")
            if len(near):
                print(near.to_string(index=False))
            print()
        except Exception as e:
            print("  ST_DWithin query failed:", e)

    # ---- 5. irrigated fields ranked by exposure ----------------------------
    if {"fields", "dams"} <= set(layers):
        q = f"""
        SELECT f.field_id,
               ROUND(f.area_km2, 3) AS area_km2,
               ROUND(MIN(ST_Distance(
                   ST_Transform(f.geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true),
                   ST_Transform(d.geom, 'EPSG:4326', 'EPSG:{UTM}', always_xy := true))) / 1000, 1) AS km_to_dam,
               ST_AsText(ST_Centroid(f.geom)) AS centroid_wkt
        FROM fields f CROSS JOIN dams d
        GROUP BY f.field_id, f.area_km2, f.geom
        ORDER BY km_to_dam
        """
        try:
            fx = con.execute(q).df()
            print("IRRIGATED FIELDS ranked by distance to the nearest dam")
            print(fx.head(8).to_string(index=False))
            print(f"  ... {len(fx):,} fields total, "
                  f"{fx['area_km2'].sum():,.0f} km2 irrigated\n")
            fx.drop(columns=["centroid_wkt"]).to_csv(
                PROCESSED / "sql_field_exposure.csv", index=False)
        except Exception as e:
            print("  field-exposure query failed:", e)

    # ---- 6. export cloud-native GeoParquet ---------------------------------
    print("exporting GeoParquet (cloud-native vector, replaces the shapefile)")
    rows = []
    for name, gdf in layers.items():
        out = PARQUET / f"{name}.parquet"
        gdf.to_parquet(out, index=False)          # GeoParquet via geopandas
        gpkg_equiv = GPKG.stat().st_size / 1e6
        rows.append({"layer": name, "features": len(gdf),
                     "parquet_mb": round(out.stat().st_size / 1e6, 3)})
        print(f"  {name:12s} {len(gdf):>6,} features -> {out.name} "
              f"({out.stat().st_size/1e6:.2f} MB)")

    pd.DataFrame(rows).to_csv(PROCESSED / "spatial_sql_report.csv", index=False)

    # verify the parquet round-trips as real geospatial data
    ok = 0
    for name in layers:
        try:
            back = gpd.read_parquet(PARQUET / f"{name}.parquet")
            assert back.crs is not None and len(back) == len(layers[name])
            ok += 1
        except Exception as e:
            print(f"  VALIDATION FAILED {name}: {e}")
    print(f"\n{ok}/{len(layers)} GeoParquet files validated (CRS + feature count preserved)")
    print("wrote data/processed/spatial_sql_report.csv")


if __name__ == "__main__":
    main()

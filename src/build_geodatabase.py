"""
build_geodatabase.py
Assemble a clean, attributed GIS geodatabase (GeoPackage) from the project's
spatial data — demonstrating GIS data entry, editing, attribute management, and
file/database organisation.

Layers written to gis/morocco_water.gpkg (all EPSG:4326):
  reservoirs   polygons  — Al Massira water extent, digitised from Sentinel-2
  dams         points    — major dams, with attributes
  communities  points    — towns depending on the water, with population

Also exports dams + reservoirs to AutoCAD DXF (gis/morocco_water.dxf) to show
CAD interoperability.
"""
from __future__ import annotations
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"
RAW = ROOT / "data" / "raw"
GIS = ROOT / "gis"
GPKG = GIS / "morocco_water.gpkg"
CRS = "EPSG:4326"


def build_reservoirs() -> gpd.GeoDataFrame:
    src = gpd.read_file(GEO / "al_massira_water.gpkg", layer="water").to_crs(CRS)
    src = src.rename(columns={"area_km2": "area_km2", "date": "obs_date"})
    src["feature_id"] = ["ALM-" + str(int(y)) for y in src["year"]]
    src["name"] = "Al Massira reservoir"
    src["method"] = "Sentinel-2 NDWI + Otsu threshold"
    src["source"] = "Copernicus Sentinel-2 L2A via Earth Search"
    cols = ["feature_id", "name", "year", "obs_date", "area_km2", "method", "source", "geometry"]
    return src[cols].set_geometry("geometry").set_crs(CRS)


def build_dams() -> gpd.GeoDataFrame:
    rows = [
        {"feature_id": "DAM-ALM", "name": "Al Massira Dam", "river": "Oum Er-Rbia",
         "dam_type": "Gravity", "commissioned": 1979, "lon": -7.625, "lat": 32.525,
         "source": "public records"},
        {"feature_id": "DAM-BEO", "name": "Bin el Ouidane Dam", "river": "El Abid",
         "dam_type": "Arch", "commissioned": 1953, "lon": -6.44, "lat": 32.10,
         "source": "public records"},
    ]
    df = pd.DataFrame(rows)
    gdf = gpd.GeoDataFrame(df, geometry=[Point(r.lon, r.lat) for r in df.itertuples()], crs=CRS)
    return gdf


def build_communities() -> gpd.GeoDataFrame:
    df = pd.read_csv(RAW / "communities_al_massira.csv", comment="#")
    df["feature_id"] = ["TOWN-" + n.split()[0].upper()[:4] for n in df["name"]]
    gdf = gpd.GeoDataFrame(
        df[["feature_id", "name", "population_2014", "role"]],
        geometry=[Point(r.lon, r.lat) for r in df.itertuples()], crs=CRS)
    return gdf


def main() -> None:
    GIS.mkdir(exist_ok=True)
    if GPKG.exists():
        GPKG.unlink()
    layers = {
        "reservoirs": build_reservoirs(),
        "dams": build_dams(),
        "communities": build_communities(),
    }
    for name, gdf in layers.items():
        gdf.to_file(GPKG, layer=name, driver="GPKG")
        print(f"layer '{name}': {len(gdf)} features, {len(gdf.columns)-1} attributes, CRS {gdf.crs.to_string()}")

    # AutoCAD DXF export (geometry only; demonstrates CAD interoperability)
    try:
        cad = pd.concat([layers["dams"][["geometry"]], layers["reservoirs"][["geometry"]]],
                        ignore_index=True)
        gpd.GeoDataFrame(cad, crs=CRS).to_file(GIS / "morocco_water.dxf", driver="DXF")
        print("exported gis/morocco_water.dxf (AutoCAD)")
    except Exception as e:  # noqa: BLE001 — DXF driver can be finicky; don't fail the build
        print("DXF export skipped:", e)

    print("wrote", GPKG.relative_to(ROOT))


if __name__ == "__main__":
    main()

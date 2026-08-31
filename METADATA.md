# Metadata & data dictionary

Documentation for the GIS geodatabase `gis/morocco_water.gpkg`. Kept deliberately
explicit — clear metadata is part of accurate, maintainable GIS data.

## Coordinate reference systems (CRS) used

Different tasks need different projections; this project is explicit about which and why.

| EPSG | Name | Used for | Why |
|------|------|----------|-----|
| **4326** | WGS 84 (lat/lon) | **storage** of all vector layers | universal, unambiguous exchange format |
| **32629** | WGS 84 / UTM zone 29N | area & distance measurement (Al Massira, argan region) | metric units, low distortion locally — correct for computing km² |
| **32630** | WGS 84 / UTM zone 30N | eastern basin work | Morocco spans UTM zones 29N and 30N (the boundary is 6°W) |
| **3857** | Web Mercator | web maps / XYZ basemaps | matches tiled basemaps (Esri, CARTO, OpenTopoMap) |

**Reprojection lineage:** raw Sentinel-2 tiles arrive in UTM (29N/30N). Water and NDVI are
measured in UTM (so areas are in true km²), then reprojected to **EPSG:4326** for storage
and to **EPSG:3857** for web display. Reprojections use `pyproj` / `rasterio.warp`.

> Note on zones: measuring area in a geographic CRS (degrees) is wrong — a degree of
> longitude is not a fixed distance. All areas here are computed in UTM, then the geometry
> is stored in 4326. This is a deliberate accuracy choice.

## Layers

### `reservoirs` — polygon
Al Massira water extent, **digitised from Sentinel-2 imagery** (NDWI + Otsu, then vectorised).

| Field | Type | Description |
|-------|------|-------------|
| feature_id | string | unique id (e.g. `ALM-2017`) |
| name | string | reservoir name |
| year | int | observation year |
| obs_date | string | acquisition date of the source scene (YYYY-MM-DD) |
| area_km2 | float | water surface area, measured in UTM 29N |
| method | string | measurement method |
| source | string | data provenance |

### `dams` — point
Major dams on the Oum Er-Rbia system.

| Field | Type | Description |
|-------|------|-------------|
| feature_id | string | unique id (e.g. `DAM-ALM`) |
| name | string | dam name |
| river | string | river dammed |
| dam_type | string | structural type (Gravity / Arch) |
| commissioned | int | year commissioned |
| lon, lat | float | coordinates (EPSG:4326) |
| source | string | data provenance |

### `communities` — point
Towns that depend on the reservoir's water.

| Field | Type | Description |
|-------|------|-------------|
| feature_id | string | unique id (e.g. `TOWN-CASA`) |
| name | string | town name |
| population_2014 | int | population, 2014 census (HCP Morocco) |
| role | string | how the town relates to the water system |

## Formats

- `gis/morocco_water.gpkg` — OGC GeoPackage (the working geodatabase)
- `gis/morocco_water.dxf` — AutoCAD DXF export (geometry), for CAD interoperability
- `data/geo/ndvi_change_argan.tif` — GeoTIFF raster (NDVI change), EPSG:4326

## Quality control

Every layer passes the automated checks in `src/qa_qc.py`; the current result is in
[QA_QC_REPORT.md](QA_QC_REPORT.md) (CRS, geometry validity, attribute completeness,
duplicate ids, coordinate range).

## GRACE and GRACE-FO water storage

**File:** `data/processed/grace_storage.csv` (516 rows)
**Made by:** `src/analysis/measure_grace.py`
**Source:** CSR GRACE/GRACE-FO RL06.03 mascons, University of Texas Center for Space Research.
Public download, no account needed. The raw file (108 MB) is not committed; the script tells you
where to get it.

| column | meaning |
|---|---|
| `region` | Souss-Massa, or Oum Er-Rbia |
| `date` | month of the solution |
| `lwe_cm` | liquid water equivalent thickness anomaly, centimetres, against the mission mean |

**Coverage:** April 2002 to 2026, 258 monthly solutions per region, with a gap through 2017 and
2018 between the two missions. The gap is left empty rather than interpolated.

**Limits, which matter here:**
- This is **total** water storage. Snow, surface water, soil moisture and groundwater are all in
  one number. Separating groundwater needs a land surface model subtracted from it, which this
  project has not done.
- The footprint is a few hundred kilometres, wider than either basin. Read it as the region a
  basin sits inside, not the basin itself.
- Values are anomalies, not absolute storage. Only the change over time means anything.

**A trap worth recording:** these files spell the time units attribute `Units` with a capital U
rather than the CF-standard `units`, so xarray does not decode the axis. Read naively, the raw
values (days since 2002-01-01) get treated as nanoseconds since 1970 and every month collapses
onto the same date. The script decodes the axis explicitly for that reason.

## Global comparison

**File:** `data/raw/global_water_comparison.csv`
**Made by:** hand, from published sources; each row carries its own citation.
**Used by:** `src/figures/build_global_context.py`

Peak and recent surface areas for the Aral Sea, Lake Chad, Lake Mead and Al Massira, with the
years measured. Only the Al Massira row comes from this project's own measurement. The others
are cited figures and are approximate, which is why the figure compares shares rather than
absolute areas.

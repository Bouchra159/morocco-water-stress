# GIS data QA/QC report

Geodatabase: `gis/morocco_water.gpkg`  ·  3 layers  ·  expected CRS **EPSG:4326**
**Result: 21/21 checks passed.**


## Layer `reservoirs`  (2 features, 7 attributes)

| Check | Result | Detail |
|---|---|---|
| CRS defined and = EPSG:4326 | ✅ PASS | EPSG:4326 |
| All geometries valid | ✅ PASS | 0 invalid |
| No empty / null geometries | ✅ PASS | 0 empty |
| Attribute 'feature_id' complete (no nulls) | ✅ PASS | 0 null/blank |
| Attribute 'name' complete (no nulls) | ✅ PASS | 0 null/blank |
| feature_id unique (no duplicates) | ✅ PASS | 0 duplicates |
| Coordinates within Morocco envelope | ✅ PASS | bounds [-7.68, 32.44, -7.48, 32.64] |

## Layer `dams`  (2 features, 8 attributes)

| Check | Result | Detail |
|---|---|---|
| CRS defined and = EPSG:4326 | ✅ PASS | EPSG:4326 |
| All geometries valid | ✅ PASS | 0 invalid |
| No empty / null geometries | ✅ PASS | 0 empty |
| Attribute 'feature_id' complete (no nulls) | ✅ PASS | 0 null/blank |
| Attribute 'name' complete (no nulls) | ✅ PASS | 0 null/blank |
| feature_id unique (no duplicates) | ✅ PASS | 0 duplicates |
| Coordinates within Morocco envelope | ✅ PASS | bounds [-7.62, 32.10, -6.44, 32.52] |

## Layer `communities`  (5 features, 4 attributes)

| Check | Result | Detail |
|---|---|---|
| CRS defined and = EPSG:4326 | ✅ PASS | EPSG:4326 |
| All geometries valid | ✅ PASS | 0 invalid |
| No empty / null geometries | ✅ PASS | 0 empty |
| Attribute 'feature_id' complete (no nulls) | ✅ PASS | 0 null/blank |
| Attribute 'name' complete (no nulls) | ✅ PASS | 0 null/blank |
| feature_id unique (no duplicates) | ✅ PASS | 0 duplicates |
| Coordinates within Morocco envelope | ✅ PASS | bounds [-8.51, 32.65, -7.59, 33.59] |

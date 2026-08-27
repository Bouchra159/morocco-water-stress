"""
qa_qc.py
Quality assurance / quality control on the GIS geodatabase — the checks a GIS
technician runs before data is accepted: coordinate reference system, geometry
validity, attribute completeness, duplicates, and coordinate range.

Reads gis/morocco_water.gpkg (run build_geodatabase.py first) and writes a
human-readable report to QA_QC_REPORT.md.
"""
from __future__ import annotations
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
GPKG = ROOT / "gis" / "morocco_water.gpkg"
REPORT = ROOT / "QA_QC_REPORT.md"

EXPECTED_CRS = "EPSG:4326"
MOROCCO_BBOX = (-17.5, 20.5, -0.5, 36.1)   # lon/lat sanity envelope
KEY_FIELDS = ("feature_id", "name")


def check_layer(gdf: gpd.GeoDataFrame) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    crs_ok = gdf.crs is not None and gdf.crs.to_string() == EXPECTED_CRS
    checks.append(("CRS defined and = EPSG:4326", crs_ok,
                   gdf.crs.to_string() if gdf.crs else "undefined"))

    n_invalid = int((~gdf.geometry.is_valid).sum())
    checks.append(("All geometries valid", n_invalid == 0, f"{n_invalid} invalid"))

    n_empty = int(gdf.geometry.is_empty.sum() + gdf.geometry.isna().sum())
    checks.append(("No empty / null geometries", n_empty == 0, f"{n_empty} empty"))

    for f in KEY_FIELDS:
        if f in gdf.columns:
            n_null = int(gdf[f].isna().sum() + (gdf[f].astype(str).str.strip() == "").sum())
            checks.append((f"Attribute '{f}' complete (no nulls)", n_null == 0, f"{n_null} null/blank"))

    if "feature_id" in gdf.columns:
        n_dup = int(gdf["feature_id"].duplicated().sum())
        checks.append(("feature_id unique (no duplicates)", n_dup == 0, f"{n_dup} duplicates"))

    minx, miny, maxx, maxy = gdf.total_bounds
    in_box = (MOROCCO_BBOX[0] <= minx and maxx <= MOROCCO_BBOX[2]
              and MOROCCO_BBOX[1] <= miny and maxy <= MOROCCO_BBOX[3])
    checks.append(("Coordinates within Morocco envelope", in_box,
                   f"bounds [{minx:.2f}, {miny:.2f}, {maxx:.2f}, {maxy:.2f}]"))
    return checks


def main() -> None:
    layers = gpd.list_layers(GPKG)["name"].tolist()
    lines = ["# GIS data QA/QC report", "",
             f"Geodatabase: `gis/morocco_water.gpkg`  ·  {len(layers)} layers  ·  "
             f"expected CRS **{EXPECTED_CRS}**", ""]
    total, passed = 0, 0
    for layer in layers:
        gdf = gpd.read_file(GPKG, layer=layer)
        lines += [f"## Layer `{layer}`  ({len(gdf)} features, {len(gdf.columns) - 1} attributes)",
                  "", "| Check | Result | Detail |", "|---|---|---|"]
        for name, ok, detail in check_layer(gdf):
            total += 1; passed += ok
            lines.append(f"| {name} | {'✅ PASS' if ok else '❌ FAIL'} | {detail} |")
        lines.append("")
    lines.insert(3, f"**Result: {passed}/{total} checks passed.**")
    lines.insert(4, "")
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"{passed}/{total} checks passed — wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

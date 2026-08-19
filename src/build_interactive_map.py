"""
build_interactive_map.py
An interactive web map built with leafmap (Qiusheng Wu's package) — the modern,
open-source Python-GIS way to share spatial work. Self-contained HTML.

Layers: Al Massira reservoir 2017 vs 2024, the communities and dams that depend on
it, and the argan-region land-cover + NDVI-change rasters as toggleable overlays.

Run: python src/build_interactive_map.py   (needs the geodatabase + rasters built)
Output: storymap/interactive_map.html
"""
from __future__ import annotations
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib
import numpy as np
import rasterio
from matplotlib.colors import Normalize

import leafmap.foliumap as leafmap

ROOT = Path(__file__).resolve().parents[1]
GIS = ROOT / "gis" / "morocco_water.gpkg"
GEO = ROOT / "data" / "geo"
OUT = ROOT / "storymap" / "interactive_map.html"

# land-cover class -> RGB (same order as classify_landcover.py)
LC_COLORS = {0: (26, 122, 58), 1: (123, 160, 90), 2: (205, 216, 154),
             3: (217, 185, 138), 4: (154, 138, 122), 5: (176, 160, 144)}


def landcover_overlay():
    with rasterio.open(GEO / "landcover_souss.tif") as src:
        lc = src.read(1)
        b = src.bounds
    rgba = np.zeros((*lc.shape, 4), "uint8")
    for v, (r, g, bl) in LC_COLORS.items():
        m = lc == v
        rgba[m] = [r, g, bl, 205]
    return rgba, [[b.bottom, b.left], [b.top, b.right]]


def ndvi_overlay():
    with rasterio.open(GEO / "ndvi_change_argan.tif") as src:
        nd = src.read(1)
        b = src.bounds
    cmap = matplotlib.colormaps["BrBG"]
    rgba = (cmap(Normalize(-0.25, 0.25)(nd)) * 255).astype("uint8")
    rgba[..., 3] = np.where(np.isfinite(nd), 185, 0)
    return rgba, [[b.bottom, b.left], [b.top, b.right]]


def main():
    m = leafmap.Map(center=[32.5, -7.6], zoom=9, control_scale=True)
    m.add_basemap("SATELLITE")
    m.add_basemap("OpenTopoMap")

    res = gpd.read_file(GIS, layer="reservoirs")
    folium.GeoJson(res[res["year"] == 2017].to_json(), name="Al Massira — 2017 shoreline",
                   style_function=lambda x: {"color": "#00e5ff", "weight": 2, "fill": False}).add_to(m)
    folium.GeoJson(res[res["year"] == 2024].to_json(), name="Al Massira — 2024 water",
                   style_function=lambda x: {"color": "#ffffff", "weight": 1,
                                             "fillColor": "#2a6f97", "fillOpacity": 0.75}).add_to(m)

    com = gpd.read_file(GIS, layer="communities")
    cg = folium.FeatureGroup(name="Communities")
    for r in com.itertuples():
        folium.CircleMarker([r.geometry.y, r.geometry.x], radius=5, color="black",
                            fill=True, fill_color="black", fill_opacity=0.9,
                            popup=f"{r.name}: {r.population_2014:,} (2014)").add_to(cg)
    cg.add_to(m)

    dams = gpd.read_file(GIS, layer="dams")
    dg = folium.FeatureGroup(name="Dams")
    for r in dams.itertuples():
        folium.Marker([r.geometry.y, r.geometry.x], popup=f"{r.name} ({r.river}, {r.commissioned})",
                      icon=folium.Icon(color="red", icon="tint", prefix="fa")).add_to(dg)
    dg.add_to(m)

    lc_img, lc_bounds = landcover_overlay()
    folium.raster_layers.ImageOverlay(lc_img, bounds=lc_bounds, opacity=0.8,
                                      name="Land cover — argan area (Sentinel-2)", show=False).add_to(m)
    nd_img, nd_bounds = ndvi_overlay()
    folium.raster_layers.ImageOverlay(nd_img, bounds=nd_bounds, opacity=0.8,
                                      name="NDVI change 2018–2024 (brown = drier)", show=False).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    try:
        from folium.plugins import Fullscreen, MiniMap
        Fullscreen().add_to(m)
        MiniMap(toggle_display=True).add_to(m)
    except Exception:
        pass

    OUT.parent.mkdir(exist_ok=True)
    m.to_html(str(OUT))
    print("wrote", OUT.relative_to(ROOT), f"({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()

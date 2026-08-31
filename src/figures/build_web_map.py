"""
build_web_map.py
An interactive web map of the Al Massira reservoir, built with MapLibre GL JS.

The print layouts in src/cartography say what happened. This lets someone look
for themselves: fade between the 2017 shoreline and the 2024 drought low over
satellite imagery, click a town to see who depends on the water, and zoom in on
the lakebed that was left behind.

It is one self-contained HTML file with the geometry embedded, so it opens from
disk, works on GitHub Pages, and needs no server and no API key.

Outputs: storymap/map.html
"""
from __future__ import annotations

import json
import os
import pathlib

import geopandas as gpd


def _repo_root():
    try:
        return pathlib.Path(__file__).resolve().parents[2]
    except NameError:
        return pathlib.Path(os.environ.get("MOROCCO_REPO", os.getcwd()))


ROOT = _repo_root()
GPKG_WATER = ROOT / "data" / "geo" / "al_massira_water.gpkg"
GPKG_MAIN = ROOT / "gis" / "morocco_water.gpkg"
OUT = ROOT / "storymap" / "map.html"

SIMPLIFY_DEG = 0.0004        # ~40 m: keeps the shoreline shape, cuts the file size


def load(path, layer, simplify=False):
    g = gpd.read_file(path, layer=layer).to_crs(4326)
    if simplify:
        g["geometry"] = g.geometry.simplify(SIMPLIFY_DEG, preserve_topology=True)
    return json.loads(g.to_json())


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    water = load(GPKG_WATER, "water", simplify=True)
    dams = load(GPKG_MAIN, "dams")
    towns = load(GPKG_MAIN, "communities")

    def year(fc, y):
        return {"type": "FeatureCollection",
                "features": [f for f in fc["features"]
                             if str(f["properties"].get("year")) == str(y)]}

    w2017, w2024 = year(water, 2017), year(water, 2024)
    kb = (len(json.dumps(water)) + len(json.dumps(dams)) + len(json.dumps(towns))) / 1024
    print(f"geometry embedded: {kb:.0f} KB")

    html = HTML.replace("__W2017__", json.dumps(w2017)) \
               .replace("__W2024__", json.dumps(w2024)) \
               .replace("__DAMS__", json.dumps(dams)) \
               .replace("__TOWNS__", json.dumps(towns))
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}  ({OUT.stat().st_size/1024:.0f} KB)")


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Al Massira: a reservoir you can look at yourself</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<style>
  :root{ --ink:#15211f; --paper:#f7f5ef; --water:#00c5ff; --deep:#005caf; --muted:#6b6b6b; }
  *{box-sizing:border-box}
  html,body{margin:0;height:100%;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;color:var(--ink)}
  #map{position:absolute;inset:0}
  .panel{position:absolute;top:14px;left:14px;z-index:2;width:310px;max-width:calc(100vw - 28px);
         background:rgba(247,245,239,.96);border:1px solid rgba(0,0,0,.12);border-radius:8px;
         padding:14px 16px;box-shadow:0 10px 30px -12px rgba(0,0,0,.5);max-height:calc(100% - 28px);overflow:auto}
  .panel h1{font-size:1.05rem;margin:0 0 .35rem;line-height:1.25}
  .panel p{font-size:.82rem;line-height:1.5;margin:.4rem 0;color:#333}
  .muted{color:var(--muted);font-size:.74rem}
  .slider{width:100%;margin:.6rem 0 .2rem}
  .ends{display:flex;justify-content:space-between;font-size:.72rem;color:var(--muted)}
  .legend{margin-top:.7rem;border-top:1px solid rgba(0,0,0,.1);padding-top:.6rem}
  .row{display:flex;align-items:center;gap:.5rem;font-size:.78rem;margin:.28rem 0}
  .sw{width:22px;height:11px;border-radius:2px;flex:none}
  .maplibregl-popup-content{font-family:inherit;font-size:.8rem;padding:9px 11px;border-radius:6px}
  .maplibregl-popup-content b{display:block;margin-bottom:2px}
  @media (max-width:640px){ .panel{width:auto;right:14px} }
</style>
</head>
<body>
<div id="map"></div>
<div class="panel">
  <h1>Al Massira, 2017 and 2024</h1>
  <p>The reservoir that holds Casablanca's drinking water. Drag the slider to fade between the
  full 2017 shoreline and what was left at the drought low in 2024.</p>
  <input class="slider" id="fade" type="range" min="0" max="100" value="100">
  <div class="ends"><span>2024 water</span><span>2017 shoreline</span></div>
  <p class="muted">It refilled to 125 km&sup2; in 2026 after record rains. This shows the low
  point, not the end of the story.</p>
  <div class="legend">
    <div class="row"><span class="sw" style="background:transparent;border:2px solid #00c5ff"></span> 2017 shoreline, 98 km&sup2;</div>
    <div class="row"><span class="sw" style="background:#005caf;opacity:.75"></span> 2024 water, 9 km&sup2;</div>
    <div class="row"><span class="sw" style="background:#c0392b;border-radius:50%;width:11px"></span> dam</div>
    <div class="row"><span class="sw" style="background:#1a1a1a;border-radius:50%;width:11px"></span> town, click for population</div>
  </div>
  <p class="muted" style="margin-top:.7rem">Water measured from Sentinel-2 (NDWI + Otsu).
  Imagery: Esri. Maps and analysis: B. Daddaoui, 2026.</p>
</div>

<script>
const W2017 = __W2017__, W2024 = __W2024__, DAMS = __DAMS__, TOWNS = __TOWNS__;

const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      sat: {
        type: 'raster', tileSize: 256, maxzoom: 18,
        tiles: ['https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
        attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'
      }
    },
    layers: [{ id: 'sat', type: 'raster', source: 'sat' }]
  },
  center: [-7.62, 32.50], zoom: 10.9, attributionControl: true
});
window._map = map;   // exposed so the map can be inspected from the console
map.addControl(new maplibregl.NavigationControl(), 'bottom-right');
map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: 'metric' }), 'bottom-left');

map.on('load', () => {
  map.addSource('w2024', { type: 'geojson', data: W2024 });
  map.addLayer({ id: 'w2024-fill', type: 'fill', source: 'w2024',
    paint: { 'fill-color': '#005caf', 'fill-opacity': 0.75 } });
  map.addLayer({ id: 'w2024-line', type: 'line', source: 'w2024',
    paint: { 'line-color': '#ffffff', 'line-width': 0.8 } });

  map.addSource('w2017', { type: 'geojson', data: W2017 });
  map.addLayer({ id: 'w2017-line', type: 'line', source: 'w2017',
    paint: { 'line-color': '#00c5ff', 'line-width': 2.2 } });

  map.addSource('dams', { type: 'geojson', data: DAMS });
  map.addLayer({ id: 'dams-pt', type: 'circle', source: 'dams',
    paint: { 'circle-radius': 6, 'circle-color': '#c0392b',
             'circle-stroke-width': 1.6, 'circle-stroke-color': '#fff' } });

  map.addSource('towns', { type: 'geojson', data: TOWNS });
  map.addLayer({ id: 'towns-pt', type: 'circle', source: 'towns',
    paint: { 'circle-radius': 5, 'circle-color': '#1a1a1a',
             'circle-stroke-width': 1.4, 'circle-stroke-color': '#fff' } });
  map.addLayer({ id: 'towns-lbl', type: 'symbol', source: 'towns',
    layout: { 'text-field': ['get', 'name'], 'text-size': 12, 'text-offset': [0, 1.1],
              'text-anchor': 'top' },
    paint: { 'text-color': '#fff', 'text-halo-color': '#000', 'text-halo-width': 1.3 } });

  // fade between the two years
  const fade = document.getElementById('fade');
  fade.addEventListener('input', e => {
    const t = +e.target.value / 100;                 // 1 = 2017, 0 = 2024
    map.setPaintProperty('w2017-line', 'line-opacity', t);
    map.setPaintProperty('w2024-fill', 'fill-opacity', 0.75 * (1 - t) + 0.25 * t);
  });

  const popup = (e, html) => new maplibregl.Popup({ offset: 10 })
    .setLngLat(e.features[0].geometry.coordinates).setHTML(html).addTo(map);

  map.on('click', 'towns-pt', e => {
    const p = e.features[0].properties;
    const pop = p.population_2014 ? Number(p.population_2014).toLocaleString() : 'n/a';
    popup(e, `<b>${p.name}</b>${pop} people (2014 census)<br>${p.role || ''}`);
  });
  map.on('click', 'dams-pt', e => {
    const p = e.features[0].properties;
    popup(e, `<b>${p.name}</b>${p.river || ''}${p.commissioned ? '<br>built ' + p.commissioned : ''}`);
  });
  ['towns-pt', 'dams-pt'].forEach(l => {
    map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer');
    map.on('mouseleave', l, () => map.getCanvas().style.cursor = '');
  });
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

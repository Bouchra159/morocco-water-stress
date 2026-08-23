"""
style_and_layout.py  (run inside ArcGIS Pro's Python window / Notebook)
Presentation-quality ArcGIS Pro cartography for the Al Massira reservoir map.

Robust against the map having been built more than once:
  - de-duplicates layers (same name loaded twice)
  - styles reservoir (2017 shoreline vs 2024 water), dams, communities
  - hides the Souss/argan rasters (NDVI change, land cover) - they have their own
    maps and do not belong on an Al Massira basin layout
  - zooms the layout to the reservoir (with a margin), reliably
  - builds a CLEAN 3-item legend (no runaway raster value list, no duplicates)
  - finished layout: title, subtitle, legend, scale bar, north arrow, credits

Run with:
  exec(open(r"C:\\Users\\BOUCHRA\\Projects\\morocco-water-stress\\arcgis\\style_and_layout.py").read())
"""
import os
import arcpy

REPO = r"C:\Users\BOUCHRA\Projects\morocco-water-stress"
OUT_PNG = os.path.join(REPO, "figures", "arcgis_al_massira_layout.png")

aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap or aprx.listMaps()[0]


# ---------------- 0. de-duplicate layers by data source (build ran twice) ----------------
seen = set()
for l in list(m.listLayers()):
    try:
        if not (l.isFeatureLayer or l.isRasterLayer):
            continue
        try:
            key = l.dataSource
        except Exception:
            key = l.name
        if key in seen:
            m.removeLayer(l)
            print("removed duplicate:", key)
        else:
            seen.add(key)
    except Exception as e:
        print("dedup skip:", e)


def get(key):
    for l in m.listLayers():
        try:
            if key in l.name.lower():
                return l
        except Exception:
            pass
    return None


res, dams, comm = get("reservoir"), get("dam"), get("communit")
ndvi, landc = get("ndvi"), get("landcover") or get("land cover") or get("land_cover")


# ---------------- 1. hide the south-region rasters on this layout ----------------
for lyr in (ndvi, landc):
    if lyr:
        try:
            lyr.visible = False
            print("hidden on layout:", lyr.name)
        except Exception as e:
            print("hide skip:", e)


# ---------------- 2. points: clean markers (no default squares) ----------------
def style_points(l, gallery, rgb, size):
    if not l:
        return
    try:
        sym = l.symbology
        try:
            sym.renderer.symbol.applySymbolFromGallery(gallery)
        except Exception:
            pass
        sym.renderer.symbol.color = {"RGB": rgb}
        sym.renderer.symbol.size = size
        try:
            sym.renderer.symbol.outlineColor = {"RGB": [255, 255, 255, 100]}
            sym.renderer.symbol.outlineWidth = 0.5
        except Exception:
            pass
        l.symbology = sym
        print("styled points:", l.name)
    except Exception as e:
        print("point style error:", e)


style_points(comm, "Circle 3", [30, 30, 30, 100], 7)
style_points(dams, "Triangle 3", [214, 39, 40, 100], 13)


# ---------------- 3. reservoir: 2017 shoreline vs 2024 water ----------------
if res:
    try:
        sym = res.symbology
        sym.updateRenderer("UniqueValueRenderer")
        sym.renderer.fields = ["year"]
        for grp in sym.renderer.groups:
            for itm in grp.items:
                yr = str(itm.values[0][0])
                if yr == "2017":
                    itm.symbol.color = {"RGB": [0, 0, 0, 0]}
                    itm.symbol.outlineColor = {"RGB": [0, 197, 255, 100]}
                    itm.symbol.outlineWidth = 1.8
                    itm.label = "2017 shoreline (full)"
                else:
                    itm.symbol.color = {"RGB": [0, 92, 175, 100]}
                    itm.symbol.outlineColor = {"RGB": [255, 255, 255, 100]}
                    itm.symbol.outlineWidth = 0.4
                    itm.label = "2024 water (drought low)"
        res.symbology = sym
        print("styled reservoir (2017 vs 2024)")
    except Exception as e:
        print("reservoir style error:", e)


# ---------------- 4. real layer names ----------------
for lyr, name in [(res, "Al Massira reservoir (2017 vs 2024)"),
                  (dams, "Major dams"), (comm, "Communities served")]:
    if lyr:
        try:
            lyr.name = name
        except Exception as e:
            print("rename skip:", e)
print("renamed layers")


# ---------------- 5. finished layout ----------------
try:
    for old in aprx.listLayouts("Al Massira*"):
        aprx.deleteItem(old)
except Exception:
    pass

try:
    lyt = aprx.createLayout(11, 8.5, "INCH", "Al Massira Layout")
    mf = lyt.createMapFrame(
        arcpy.Polygon(arcpy.Array([arcpy.Point(0.35, 0.35), arcpy.Point(0.35, 7.7),
                                   arcpy.Point(7.9, 7.7), arcpy.Point(7.9, 0.35)])), m, "MainMap")

    # ---- reliable zoom: set camera centre + scale in the map's own SR ----
    def zoom_to_reservoir():
        try:
            sr = mf.map.spatialReference
            code = sr.factoryCode
            print("  map SR:", code, sr.name)
            if code in (3857, 102100):                 # Web Mercator
                cx, cy = -842700.0, 3841000.0          # Al Massira centre
            elif code == 4326:                         # WGS84 degrees
                cx, cy = -7.57, 32.53
            else:                                      # anything else: project a point
                pg = arcpy.PointGeometry(arcpy.Point(-7.57, 32.53),
                                         arcpy.SpatialReference(4326)).projectAs(sr)
                cx, cy = pg.centroid.X, pg.centroid.Y
            mf.camera.X = cx
            mf.camera.Y = cy
            mf.camera.scale = 380000                   # ~65 km wide on this frame
            print("  camera centre", round(cx, 1), round(cy, 1), "scale 380000")
        except Exception as e:
            print("  zoom failed:", e)

    zoom_to_reservoir()

    def surround(kind, pt, cat, name):
        try:
            items = aprx.listStyleItems("ArcGIS 2D", cat)
            return lyt.createMapSurroundElement(pt, kind, mf, items[0] if items else None, name)
        except Exception as e:
            print("  ", kind, "skipped:", e)
            return None

    leg = surround("LEGEND", arcpy.Point(8.15, 5.4), "LEGEND", "Legend")
    surround("SCALE_BAR", arcpy.Point(0.55, 0.55), "Scale_bar", "Scale Bar")
    surround("NORTH_ARROW", arcpy.Point(10.5, 7.6), "North_Arrow", "North Arrow")

    # ---- CLEAN legend: keep only the 3 vector layers, drop rasters/basemap/dupes ----
    if leg:
        try:
            keep = ("reservoir", "dam", "communit")
            cim = leg.getDefinition("V3")
            cim.items = [it for it in cim.items if any(k in it.name.lower() for k in keep)]
            try:
                cim.fittingStrategy = "AdjustFrame"
            except Exception:
                pass
            leg.setDefinition(cim)
            print("cleaned legend ->", [i.name for i in cim.items])
        except Exception as e:
            print("  legend clean skipped:", e)

    # ---- title / subtitle / credits via CIM (no createTextElement dependency) ----
    try:
        def _txt(s, x, y, h):
            return {"type": "CIMGraphicElement", "name": s[:24], "anchor": "BottomLeftCorner",
                    "graphic": {"type": "CIMTextGraphic", "text": s, "shape": {"x": x, "y": y},
                                "symbol": {"type": "CIMSymbolReference", "symbol": {
                                    "type": "CIMTextSymbol", "fontFamilyName": "Tahoma", "height": h,
                                    "symbol": {"type": "CIMPolygonSymbol", "symbolLayers": [
                                        {"type": "CIMSolidFill", "enable": True,
                                         "color": {"type": "CIMRGBColor", "values": [30, 30, 30, 100]}}]}}}}}
        cim = lyt.getDefinition("V3")
        cim.elements.append(_txt("Al Massira Reservoir - collapse and comeback", 0.35, 8.15, 22))
        cim.elements.append(_txt("Satellite water-mapping of the reservoir that waters Casablanca and the Doukkala plain", 0.35, 7.86, 11))
        cim.elements.append(_txt("Data: Sentinel-2 (Copernicus), HCP census. Cartography: B. Daddaoui, 2026.", 0.35, 0.12, 8))
        lyt.setDefinition(cim)
        print("added title / subtitle / credits")
    except Exception as e:
        print("  titles skipped:", e)

    lyt.exportToPNG(OUT_PNG, resolution=200)
    print("exported layout ->", OUT_PNG)
except Exception as e:
    print("layout error (symbology still applied):", e)

print("STYLING DONE")

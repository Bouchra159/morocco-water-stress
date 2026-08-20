"""
style_and_layout.py  (run inside ArcGIS Pro's Python window / Notebook)
Give every layer real, aesthetic cartography — no more default squares — then
build and export a finished layout. Robust: each step is independent, so styling
still applies even if the layout step has trouble.

Run after build_arcgis_project.py, same map:
  exec(open(r"C:\\Users\\BOUCHRA\\Projects\\morocco-water-stress\\arcgis\\style_and_layout.py").read())
"""
import os
import arcpy

REPO = r"C:\Users\BOUCHRA\Projects\morocco-water-stress"
OUT_PNG = os.path.join(REPO, "figures", "arcgis_al_massira_layout.png")

aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap or aprx.listMaps()[0]


def get(prefix):
    for l in m.listLayers():
        if l.name.lower().startswith(prefix):
            return l
    return None


def first_ramp(names):
    for n in names:
        r = aprx.listColorRamps(n)
        if r:
            return r[0]
    return None


# ---------- POINTS: fix the squares -> nice markers ----------
def style_points(prefix, gallery, rgb, size, outline_w=0.5):
    l = get(prefix)
    if not l:
        return
    try:
        sym = l.symbology
        try:
            sym.renderer.symbol.applySymbolFromGallery(gallery)
        except Exception as e:
            print("  (gallery symbol skipped:", e, ")")
        sym.renderer.symbol.color = {"RGB": rgb}
        sym.renderer.symbol.size = size
        try:
            sym.renderer.symbol.outlineColor = {"RGB": [255, 255, 255, 100]}
            sym.renderer.symbol.outlineWidth = outline_w
        except Exception:
            pass
        l.symbology = sym
        print("styled points:", l.name)
    except Exception as e:
        print("point style error", prefix, ":", e)


style_points("communities", "Circle 3", [30, 30, 30, 100], 8)
style_points("dams", "Triangle 3", [214, 39, 40, 100], 13)


# ---------- RESERVOIRS: 2017 shoreline vs 2024 water ----------
res = get("reservoirs")
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
                    itm.symbol.outlineWidth = 1.6
                    itm.label = "2017 shoreline (full)"
                else:
                    itm.symbol.color = {"RGB": [0, 92, 175, 100]}
                    itm.symbol.outlineColor = {"RGB": [255, 255, 255, 100]}
                    itm.symbol.outlineWidth = 0.4
                    itm.label = "2024 water (drought low)"
        res.symbology = sym
        print("styled reservoirs (2017 vs 2024)")
    except Exception as e:
        print("reservoir style error:", e)


# ---------- RASTERS: meaningful colour, not grey squares ----------
lyr = get("ndvi_change")
if lyr:
    try:
        sym = lyr.symbology
        if sym.colorizer.type != "RasterStretchColorizer":
            sym.updateColorizer("RasterStretchColorizer")
        sym.colorizer.stretchType = "PercentClip"
        ramp = first_ramp(["Brown to Green (Continuous)", "Green-Brown (Continuous)",
                           "Red-Green (Continuous)"])
        if ramp:
            sym.colorizer.colorRamp = ramp
        lyr.symbology = sym
        print("styled ndvi_change raster")
    except Exception as e:
        print("ndvi raster error:", e)

lyr = get("landcover")
if lyr:
    try:
        sym = lyr.symbology
        if sym.colorizer.type != "RasterUniqueValueColorizer":
            sym.updateColorizer("RasterUniqueValueColorizer")
        sym.colorizer.field = "Value"
        ramp = first_ramp(["Muted Pastels", "Bold", "Basic Random"])
        if ramp:
            sym.colorizer.colorRamp = ramp
        lyr.symbology = sym
        print("styled landcover raster")
    except Exception as e:
        print("landcover raster error:", e)


# ---------- zoom the map view to the reservoir ----------
try:
    view = aprx.activeView
    if res and view and hasattr(view, "camera"):
        view.camera.setExtent(view.getLayerExtent(res, False, True))
        print("zoomed to reservoir")
except Exception as e:
    print("zoom skipped:", e)


# ---------- layout + export (best effort) ----------
try:
    for old in aprx.listLayouts("Al Massira*"):
        aprx.deleteItem(old)
except Exception:
    pass
try:
    lyt = aprx.createLayout(11, 8.5, "INCH", "Al Massira Layout")
    mf = lyt.createMapFrame(
        arcpy.Polygon(arcpy.Array([arcpy.Point(0.4, 0.4), arcpy.Point(0.4, 8.1),
                                   arcpy.Point(7.7, 8.1), arcpy.Point(7.7, 0.4)])), m, "MainMap")
    if res:
        mf.camera.setExtent(mf.getLayerExtent(res, False, True))

    def surround(kind, pt, cat):
        items = aprx.listStyleItems("ArcGIS 2D", cat)
        try:
            lyt.createMapSurroundElement(pt, kind, mf, items[0] if items else None,
                                         kind.title().replace("_", " "))
        except Exception as e:
            print("  (", kind, "skipped:", e, ")")

    surround("LEGEND", arcpy.Point(8.0, 6.2), "LEGEND")
    surround("SCALE_BAR", arcpy.Point(0.6, 0.55), "Scale_bar")
    surround("NORTH_ARROW", arcpy.Point(10.3, 7.6), "North_Arrow")

    ttl = lyt.createTextElement(arcpy.Point(0.4, 8.2),
                                "Al Massira Reservoir & the Oum Er-Rbia \u2014 a GIS analysis")
    ttl.textSize = 20
    lyt.exportToPNG(OUT_PNG, resolution=200)
    print("exported layout ->", OUT_PNG)
except Exception as e:
    print("layout error (symbology still applied):", e)

print("STYLING DONE")

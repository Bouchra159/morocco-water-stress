"""
style_and_layout.py  (run inside ArcGIS Pro's Python window)
Style the loaded layers and export a finished cartographic layout — automated
with arcpy. Inspired by beautiful-cartography practice (John Nelson / Esri).

Run after build_arcgis_project.py, in the same map:
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


# ---------- raster symbology ----------
lyr = get("ndvi_change")
if lyr:
    try:
        sym = lyr.symbology
        if sym.colorizer.type != "RasterStretchColorizer":
            sym.updateColorizer("RasterStretchColorizer")
        sym.colorizer.stretchType = "PercentClip"
        ramp = first_ramp(["Brown to Green (Continuous)", "Green-Brown (Continuous)",
                           "Red-Green (Continuous)", "Cyan to Purple"])
        if ramp:
            sym.colorizer.colorRamp = ramp
        lyr.symbology = sym
        print("styled ndvi_change (stretch)")
    except Exception as e:
        print("ndvi sym error:", e)

lyr = get("landcover")
if lyr:
    try:
        sym = lyr.symbology
        if sym.colorizer.type != "RasterUniqueValueColorizer":
            sym.updateColorizer("RasterUniqueValueColorizer")
        sym.colorizer.field = "Value"
        ramp = first_ramp(["Muted Pastels", "Basic Random", "Bold"])
        if ramp:
            sym.colorizer.colorRamp = ramp
        lyr.symbology = sym
        print("styled landcover (unique value)")
    except Exception as e:
        print("landcover sym error:", e)


# ---------- vector symbology ----------
def color_vec(prefix, rgb, size=None):
    l = get(prefix)
    if not l:
        return
    try:
        sym = l.symbology
        sym.renderer.symbol.color = {"RGB": rgb}
        if size:
            sym.renderer.symbol.size = size
        l.symbology = sym
        print("styled", l.name)
    except Exception as e:
        print("vec sym error", prefix, ":", e)


color_vec("reservoirs", [0, 92, 175, 100])
color_vec("dams", [214, 39, 40, 100], 12)
color_vec("communities", [20, 20, 20, 100], 8)


# ---------- layout + export ----------
try:
    for existing in aprx.listLayouts("Al Massira*"):
        pass
    lyt = aprx.createLayout(11, 8.5, "INCH", "Al Massira Layout")
    mf = lyt.createMapFrame(
        arcpy.Polygon(arcpy.Array([arcpy.Point(0.4, 0.4), arcpy.Point(0.4, 8.1),
                                   arcpy.Point(7.7, 8.1), arcpy.Point(7.7, 0.4)])), m, "MainMap")
    res = get("reservoirs")
    if res:
        mf.camera.setExtent(mf.getLayerExtent(res, False, True))

    def surround(kind, poly, style_cat):
        items = aprx.listStyleItems("ArcGIS 2D", style_cat)
        si = items[0] if items else None
        return lyt.createMapSurroundElement(poly, kind, mf, si,
                                            kind.title().replace("_", " "))

    surround("LEGEND", arcpy.Point(7.9, 6.0), "LEGEND")
    surround("SCALE_BAR", arcpy.Point(0.6, 0.55), "Scale_bar")
    surround("NORTH_ARROW", arcpy.Point(10.4, 7.6), "North_Arrow")

    ttl = lyt.createTextElement(arcpy.Point(0.4, 8.2), "Al Massira & the Oum Er-Rbia — GIS analysis")
    ttl.textSize = 22

    lyt.exportToPNG(OUT_PNG, resolution=200)
    print("exported layout ->", OUT_PNG)
except Exception as e:
    print("layout error:", e)

print("done")

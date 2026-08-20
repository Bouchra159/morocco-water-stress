"""
style_and_layout.py  (run inside ArcGIS Pro's Python window / Notebook)
Complete, presentation-quality cartography for the Morocco_Water map:
  - real layer names (not file names)
  - aesthetic symbology (no default squares)
  - a fully labelled land-cover legend (named classes, not "Value 0,1,2...")
  - reservoir shown as 2017 shoreline vs 2024 water
  - a finished layout: title, subtitle, legend, scale bar, north arrow, credits

Every step is independent (try/except) so partial success is fine. Run with:
  exec(open(r"C:\\Users\\BOUCHRA\\Projects\\morocco-water-stress\\arcgis\\style_and_layout.py").read())
"""
import os
import arcpy

REPO = r"C:\Users\BOUCHRA\Projects\morocco-water-stress"
OUT_PNG = os.path.join(REPO, "figures", "arcgis_al_massira_layout.png")

aprx = arcpy.mp.ArcGISProject("CURRENT")
m = aprx.activeMap or aprx.listMaps()[0]

# land-cover classes: raster Value -> (label, RGB)   (order from classify_landcover.py)
LC = {0: ("Irrigated / dense vegetation", [26, 122, 58]),
      1: ("Argan woodland / shrub", [123, 160, 90]),
      2: ("Sparse vegetation", [205, 216, 154]),
      3: ("Bare soil", [217, 185, 138]),
      4: ("Rock / mountain", [154, 138, 122]),
      5: ("Other / mixed", [176, 160, 144])}


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


# grab references up front (so renaming later doesn't break lookups)
res, dams, comm = get("reservoirs"), get("dams"), get("communities")
ndvi, landc = get("ndvi_change"), get("landcover")


# ---------------- points: fix squares -> clean markers ----------------
def style_points(l, gallery, rgb, size):
    if not l:
        return
    try:
        sym = l.symbology
        try:
            sym.renderer.symbol.applySymbolFromGallery(gallery)
        except Exception as e:
            print("  gallery skipped:", e)
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


style_points(comm, "Circle 3", [30, 30, 30, 100], 8)
style_points(dams, "Triangle 3", [214, 39, 40, 100], 13)


# ---------------- reservoir: 2017 shoreline vs 2024 water ----------------
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
        print("styled reservoir (2017 vs 2024)")
    except Exception as e:
        print("reservoir style error:", e)


# ---------------- NDVI change raster ----------------
if ndvi:
    try:
        sym = ndvi.symbology
        if sym.colorizer.type != "RasterStretchColorizer":
            sym.updateColorizer("RasterStretchColorizer")
        sym.colorizer.stretchType = "PercentClip"
        ramp = first_ramp(["Brown to Green (Continuous)", "Green-Brown (Continuous)",
                           "Red-Green (Continuous)"])
        if ramp:
            sym.colorizer.colorRamp = ramp
        ndvi.symbology = sym
        print("styled NDVI change raster")
    except Exception as e:
        print("ndvi raster error:", e)


# ---------------- land cover: named classes + colours ----------------
if landc:
    try:
        sym = landc.symbology
        if sym.colorizer.type != "RasterUniqueValueColorizer":
            sym.updateColorizer("RasterUniqueValueColorizer")
        sym.colorizer.field = "Value"
        for grp in sym.colorizer.groups:
            for itm in grp.items:
                try:
                    v = int(float(itm.values[0]))
                except Exception:
                    continue
                if v in LC:
                    itm.label = LC[v][0]
                    itm.color = {"RGB": LC[v][1] + [100]}
        landc.symbology = sym
        print("styled land cover (named classes)")
    except Exception as e:
        print("landcover raster error:", e)


# ---------------- real layer names (do this last) ----------------
for lyr, name in [(res, "Al Massira reservoir (2017 vs 2024)"),
                  (dams, "Major dams"),
                  (comm, "Communities served"),
                  (ndvi, "Vegetation change 2018\u20132026 (NDVI)"),
                  (landc, "Land cover (Sentinel-2, 2026)")]:
    if lyr:
        try:
            lyr.name = name
        except Exception as e:
            print("rename skipped:", e)
print("renamed layers")


# ---------------- zoom to the reservoir ----------------
try:
    view = aprx.activeView
    if res and view and hasattr(view, "camera"):
        view.camera.setExtent(view.getLayerExtent(res, False, True))
        print("zoomed to reservoir")
except Exception as e:
    print("zoom skipped:", e)


# ---------------- finished layout ----------------
try:
    for old in aprx.listLayouts("Al Massira*"):
        aprx.deleteItem(old)
except Exception:
    pass
try:
    lyt = aprx.createLayout(11, 8.5, "INCH", "Al Massira Layout")
    mf = lyt.createMapFrame(
        arcpy.Polygon(arcpy.Array([arcpy.Point(0.35, 0.35), arcpy.Point(0.35, 7.7),
                                   arcpy.Point(7.6, 7.7), arcpy.Point(7.6, 0.35)])), m, "MainMap")
    if res:
        mf.camera.setExtent(mf.getLayerExtent(res, False, True))

    def surround(kind, pt, cat, name):
        try:
            items = aprx.listStyleItems("ArcGIS 2D", cat)
            lyt.createMapSurroundElement(pt, kind, mf, items[0] if items else None, name)
            print("  added", name)
        except Exception as e:
            print("  ", kind, "skipped:", e)

    surround("LEGEND", arcpy.Point(7.8, 5.6), "LEGEND", "Legend")
    surround("SCALE_BAR", arcpy.Point(0.55, 0.5), "Scale_bar", "Scale Bar")
    surround("NORTH_ARROW", arcpy.Point(10.4, 7.5), "North_Arrow", "North Arrow")

    def text(pt, s, size, bold=False):
        try:
            t = lyt.createTextElement(pt, s)
            t.textSize = size
            return t
        except Exception as e:
            print("  text skipped:", e)

    text(arcpy.Point(0.35, 8.15), "Al Massira Reservoir & the Oum Er-Rbia Basin", 22)
    text(arcpy.Point(0.35, 7.85), "Satellite water-mapping, land cover and the communities that depend on it", 12)
    text(arcpy.Point(0.35, 0.18),
         "Data: Sentinel-2 (Copernicus), Copernicus DEM, HCP census. Analysis & cartography: B. Daddaoui, 2026.", 8)

    lyt.exportToPNG(OUT_PNG, resolution=200)
    print("exported layout ->", OUT_PNG)
except Exception as e:
    print("layout error (symbology still applied):", e)

print("STYLING DONE")

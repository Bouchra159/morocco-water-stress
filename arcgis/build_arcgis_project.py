"""
build_arcgis_project.py
Build an ArcGIS Pro map from this project's GIS data, using arcpy — so the whole
geodatabase and the analysis rasters load and symbolise in one step.

HOW TO RUN (inside ArcGIS Pro):
  1. ArcGIS Pro -> New -> Map (create/open any project).
  2. Analysis tab -> Python, or View -> Python window.
  3. Run this file:  exec(open(r"C:\\Users\\BOUCHRA\\Projects\\morocco-water-stress\\arcgis\\build_arcgis_project.py").read())
     (or open it in the Python window and run).

It adds the reservoirs / dams / communities layers from the GeoPackage and the
NDVI-change and land-cover rasters, then zooms to them. arcpy only runs inside
ArcGIS Pro (it ships with Pro's Python), not in a normal Python install.
"""
import os
import arcpy

REPO = r"C:\Users\BOUCHRA\Projects\morocco-water-stress"
GPKG = os.path.join(REPO, "gis", "morocco_water.gpkg")
GEO = os.path.join(REPO, "data", "geo")

VECTOR_LAYERS = ["main.reservoirs", "main.dams", "main.communities"]
RASTERS = [
    os.path.join(GEO, "ndvi_change_argan.tif"),
    os.path.join(GEO, "landcover_souss.tif"),
]


def main():
    aprx = arcpy.mp.ArcGISProject("CURRENT")
    m = aprx.activeMap or aprx.listMaps()[0]
    print("Active map:", m.name)

    added = []
    for lyr in VECTOR_LAYERS:
        path = os.path.join(GPKG, lyr)
        try:
            m.addDataFromPath(path)
            added.append(lyr)
            print("added vector:", lyr)
        except Exception as e:  # keep going if one layer is missing
            print("skip", lyr, "->", e)

    for r in RASTERS:
        if os.path.exists(r):
            try:
                m.addDataFromPath(r)
                added.append(os.path.basename(r))
                print("added raster:", os.path.basename(r))
            except Exception as e:
                print("skip", r, "->", e)
        else:
            print("raster not found (run the Python pipeline first):", r)

    # set a sensible reference scale / zoom to the data
    try:
        view = aprx.activeView
        if view and view.__class__.__name__ == "MapView":
            ext = None
            for lyr in m.listLayers():
                try:
                    d = arcpy.Describe(lyr)
                    ext = d.extent if ext is None else ext.union(d.extent)
                except Exception:
                    pass
            if ext:
                view.camera.setExtent(ext)
                print("zoomed to data extent")
    except Exception as e:
        print("zoom skipped:", e)

    print("done — added:", ", ".join(added))
    print("Tip: right-click each layer -> Symbology to style it, then Insert -> New Layout "
          "for a cartographic output with legend, scale bar and north arrow.")


if __name__ == "__main__":
    main()
else:
    main()

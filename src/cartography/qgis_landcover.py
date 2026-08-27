"""
qgis_landcover.py  (run inside QGIS: Plugins -> Python Console)
Professional QGIS print layout of the unsupervised land-cover classification
near Taroudant (Souss / argan area), from data/geo/landcover_souss.tif.

Output: figures/map_qgis_landcover.png (300 dpi), qgis/landcover.qgz
"""
import os
import pathlib


def _repo_root():
    """Repo root, whether run as a script or pasted into the QGIS console."""
    try:
        return str(pathlib.Path(__file__).resolve().parents[2])
    except NameError:
        return os.environ.get("MOROCCO_REPO", os.getcwd())


from qgis.core import (
    QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsRectangle, QgsPalettedRasterRenderer, QgsPrintLayout, QgsLayoutItemMap,
    QgsLayoutItemLabel, QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication, QgsFillSymbol)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = _repo_root()
TIF = REPO + "/data/geo/landcover_souss.tif"
AOI = (-8.62, 30.15, -8.28, 30.52)
MM = QgsUnitTypes.LayoutMillimeters
# value -> (label, colour, area km2)   (order fixed by classify_landcover.py)
CLASSES = [
    (0, "Irrigated / dense vegetation", "#1a7a3a", 173),
    (1, "Argan woodland / shrub", "#7ba05a", 176),
    (2, "Sparse vegetation", "#cdd89a", 341),
    (3, "Bare soil", "#d9b98a", 337),
    (4, "Rock / mountain", "#9a8a7a", 144),
    (5, "Other / mixed", "#b0a090", 165)]


def main():
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    r = QgsRasterLayer(TIF, "Land cover (Sentinel-2, 2026)")
    classes = [QgsPalettedRasterRenderer.Class(v, QColor(c), lab) for v, lab, c, _ in CLASSES]
    r.setRenderer(QgsPalettedRasterRenderer(r.dataProvider(), 1, classes))
    proj.addMapLayer(r)

    xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*AOI))
    canvas = iface.mapCanvas(); canvas.setLayers([r]); canvas.setExtent(ext); canvas.refresh(); canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for l in mgr.printLayouts():
        mgr.removeLayout(l)
    layout = QgsPrintLayout(proj); layout.initializeDefaults(); layout.setName("LandCover")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM)); mgr.addLayout(layout)

    def label(t, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout); it.setText(t)
        fn = QFont("Arial"); fn.setPointSizeF(float(size)); fn.setBold(bold); it.setFont(fn)
        it.setFontColor(QColor(color)); it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM)); layout.addLayoutItem(it); return it

    m = QgsLayoutItemMap(layout); m.attemptSetSceneRect(QRectF(8, 30, 292, 258))
    m.setLayers([r]); m.setExtent(ext); m.setFrameEnabled(True); m.setFrameStrokeColor(QColor("#333"))
    layout.addLayoutItem(m)
    label("Land Cover of the Argan Country", 8, 6, 26, bold=True, color="#2c5a2c")
    label("Unsupervised classification (Sentinel-2 K-means, spring 2026) \u2014 the Souss / Anti-Atlas slopes near Taroudant",
          9, 19, 12, color="#444")

    panel = QgsLayoutItemShape(layout); panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple({"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label("Six spectral bands and three indices (NDVI, NDWI, NDBI) grouped into land-cover classes, "
          "then labelled by signature. This is where the argan woodland holds the soil \u2014 and where it "
          "is thinning to bare ground.", 312, 38, 10.5, color="#333", width=97)
    label("Land-cover class  (area)", 312, 74, 11, bold=True, color="#20140c")
    y = 84
    for _, lab, col, km2 in CLASSES:
        sq = QgsLayoutItemShape(layout); sq.setShapeType(QgsLayoutItemShape.Rectangle)
        sq.attemptSetSceneRect(QRectF(312, y, 10, 6))
        sq.setSymbol(QgsFillSymbol.createSimple({"color": col, "outline_color": "#c8c8c8", "outline_width": "0.2"}))
        layout.addLayoutItem(sq)
        label(f"{lab}   ({km2} km\u00b2)", 325, y + 0.6, 9, color="#3a2c1e", width=85)
        y += 7.2
    label("Unsupervised classification with spectrally-interpreted labels \u2014 not ground-truthed.",
          312, y + 4, 8.5, color="#777", width=97)

    sb = QgsLayoutItemScaleBar(layout); sb.setStyle("Single Box"); sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers); sb.setUnitLabel("km")
    sb.setNumberOfSegments(4); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(2)
    sb.setFont(QFont("Arial", 9)); sb.update(); sb.attemptMove(QgsLayoutPoint(312, 168, MM))
    layout.addLayoutItem(sb)
    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM)); na.attemptMove(QgsLayoutPoint(390, 162, MM))
    layout.addLayoutItem(na)
    label("Method: MiniBatch K-means on Sentinel-2 L2A surface reflectance + indices, cloud-masked (SCL). "
          "Cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777", width=300)

    png = REPO + "/figures/map_qgis_landcover.png"
    exp = QgsLayoutExporter(layout); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 300
    print("export:", exp.exportToImage(png, st))
    proj.write(REPO + "/qgis/landcover.qgz")


main()

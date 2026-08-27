"""
qgis_reservoir_layout.py
Build the high-resolution QGIS print layout of the Al Massira reservoir
(2017 shoreline vs 2024 water) over satellite imagery, and export it at 300 dpi.

Runs inside QGIS (Plugins -> Python Console). Tested on QGIS 3.40.
Requires data/geo/al_massira_water.gpkg — run src/export_reservoir_vectors.py first.

Outputs:
  figures/map_al_massira_layout.png   (300 dpi)
  figures/map_al_massira_layout.pdf
  qgis/al_massira_reservoir.qgz
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
    Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle,
    QgsFillSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape,
    QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication,
)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = _repo_root()
GPKG = REPO + "/data/geo/al_massira_water.gpkg"
MM = QgsUnitTypes.LayoutMillimeters
EXTENT_LL = (-7.74, 32.415, -7.42, 32.665)  # lon/lat map extent


def build():
    proj = QgsProject.instance()
    proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    sat = QgsRasterLayer(
        "type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=19&zmin=0",
        "Esri World Imagery", "wms")
    proj.addMapLayer(sat)

    w2017 = QgsVectorLayer(GPKG + "|layername=water", "Shoreline 2017 (98 km²)", "ogr")
    w2017.setSubsetString("year=2017")
    w2017.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "0,229,255,255", "outline_width": "0.7"})))
    proj.addMapLayer(w2017)

    w2024 = QgsVectorLayer(GPKG + "|layername=water", "Water 2024 (9 km²)", "ogr")
    w2024.setSubsetString("year=2024")
    w2024.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "42,111,151,200", "outline_color": "255,255,255,255", "outline_width": "0.3"})))
    proj.addMapLayer(w2024)

    dam = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(30)", "Al Massira Dam", "memory")
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-7.625, 32.525)))
    f.setAttributes(["Al Massira Dam"])
    dam.dataProvider().addFeature(f)
    dam.updateExtents()
    dam.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "triangle", "color": "179,38,30,255", "size": "4",
         "outline_color": "white", "outline_width": "0.5"})))
    proj.addMapLayer(dam)
    return proj, [dam, w2024, w2017, sat]


def layout_and_export(proj, order):
    xform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*EXTENT_LL))

    # warm the XYZ tile cache before the headless export
    canvas = iface.mapCanvas()
    canvas.setLayers(order)
    canvas.setExtent(ext)
    canvas.refresh()
    canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for lay in mgr.printLayouts():
        mgr.removeLayout(lay)
    layout = QgsPrintLayout(proj)
    layout.initializeDefaults()
    layout.setName("AlMassira")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM))
    mgr.addLayout(layout)

    def label(text, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout)
        it.setText(text)
        fnt = QFont("Arial", size)
        fnt.setBold(bold)
        it.setFont(fnt)
        it.setFontColor(QColor(color))
        it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM))
        layout.addLayoutItem(it)
        return it

    m = QgsLayoutItemMap(layout)
    m.attemptSetSceneRect(QRectF(8, 30, 292, 258))
    m.setLayers(order)
    m.setBackgroundColor(QColor(20, 20, 20))
    m.setExtent(ext)
    m.setFrameEnabled(True)
    m.setFrameStrokeColor(QColor("#333333"))
    layout.addLayoutItem(m)

    label("A Reservoir Vanishing", 8, 6, 30, bold=True, color="#0d3b5c")
    label("Al Massira, Morocco — measured from Sentinel-2 satellite imagery, 2017 vs 2024",
          9, 20, 13, color="#444444")

    panel = QgsLayoutItemShape(layout)
    panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 250))
    panel.setSymbol(QgsFillSymbol.createSimple(
        {"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)

    label("−91%", 312, 36, 44, bold=True, color="#b3261e")
    label("of the reservoir's water surface\nlost between 2017 and 2024",
          312, 63, 11, color="#333333", width=95)
    label("98 km²  →  9 km²", 312, 83, 13, bold=True, color="#0d3b5c", width=95)

    leg = QgsLayoutItemLegend(layout)
    leg.setLinkedMap(m)
    leg.setTitle("Water extent")
    leg.setAutoUpdateModel(False)
    root = leg.model().rootGroup()
    for node in list(root.children()):
        if node.name() == "Esri World Imagery":
            root.removeChildNode(node)
    leg.attemptMove(QgsLayoutPoint(312, 100, MM))
    layout.addLayoutItem(leg)

    sb = QgsLayoutItemScaleBar(layout)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setNumberOfSegments(3)
    sb.setNumberOfSegmentsLeft(0)
    sb.setUnitsPerSegment(2)
    sb.setFont(QFont("Arial", 9))
    sb.update()
    sb.attemptMove(QgsLayoutPoint(312, 250, MM))
    layout.addLayoutItem(sb)

    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM))
    na.attemptMove(QgsLayoutPoint(390, 244, MM))
    layout.addLayoutItem(na)

    label("Method: NDWI + Otsu on Sentinel-2 L2A (dry-season), cloud-masked with SCL.  "
          "Imagery: Sentinel-2 / Copernicus via Earth Search.  Basemap: Esri World Imagery.  "
          "Analysis & cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777777", width=300)

    exporter = QgsLayoutExporter(layout)
    s = QgsLayoutExporter.ImageExportSettings()
    s.dpi = 300
    exporter.exportToImage(REPO + "/figures/map_al_massira_layout.png", s)
    ps = QgsLayoutExporter.PdfExportSettings()
    ps.dpi = 300
    exporter.exportToPdf(REPO + "/figures/map_al_massira_layout.pdf", ps)
    proj.write(REPO + "/qgis/al_massira_reservoir.qgz")
    print("exported PNG + PDF at 300 dpi and saved project")


if __name__ == "__main__" or True:
    _proj, _order = build()
    layout_and_export(_proj, _order)

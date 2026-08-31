"""
qgis_water_journey.py
"The Water Journey" — a shaded-relief + hypsometric-tint map of the Oum Er-Rbia
headwaters, showing how Middle Atlas snowmelt feeds the Al Massira reservoir.

This is the cartographic technique used in award-winning physical maps: an
elevation colour ramp (hypsometric tint) laid over a hillshade of the terrain.

Runs inside QGIS (Plugins -> Python Console). Tested on QGIS 3.40. Needs:
  data/dem/oer_dem.tif            (run src/fetch_dem.py first)
  data/geo/al_massira_water.gpkg  (run src/export_reservoir_vectors.py)

Outputs: figures/map_water_journey.png (300 dpi) + .pdf, qgis/water_journey.qgz
"""

import os
import pathlib


def _repo_root():
    """Repo root, whether run as a script or pasted into the QGIS console."""
    try:
        return str(pathlib.Path(__file__).resolve().parents[2])
    except NameError:
        return os.environ.get("MOROCCO_REPO", os.getcwd())


import processing
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent) if "__file__" in dir() else ".")
from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle,
    QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer,
    QgsFillSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsPalLayerSettings,
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication,
)
from qgis.PyQt.QtGui import QColor, QFont, QPainter
from qgis.PyQt.QtCore import QRectF

REPO = _repo_root()
DEM = REPO + "/data/dem/oer_dem.tif"
HS = REPO + "/data/dem/oer_hillshade.tif"
GPKG = REPO + "/data/geo/al_massira_water.gpkg"
MM = QgsUnitTypes.LayoutMillimeters
EXTENT_LL = (-7.95, 32.05, -6.15, 33.75)

HYPSO = [(0, "#d8c9a0"), (150, "#dcc892"), (350, "#d8bc80"), (600, "#cda869"),
         (900, "#bf925a"), (1300, "#a97a4a"), (1800, "#9a6c44"), (2300, "#95806e"),
         (2800, "#c9bdae"), (3150, "#f4f0ea")]
LEGEND_SWATCHES = [(0, "#d8c9a0"), (600, "#cda869"), (1200, "#b0824e"),
                   (1800, "#9a6c44"), (2500, "#a08a78"), (3100, "#e9e2d6")]
CITIES = [("Casablanca", -7.59, 33.57), ("Settat", -7.62, 33.00),
          ("Beni Mellal", -6.36, 32.34), ("Kasba Tadla", -6.27, 32.60)]
DAMS = [("Al Massira Dam", -7.625, 32.525), ("Bin el Ouidane Dam", -6.44, 32.10)]


def points(proj, name, rows, color, shape, size, labelcolor):
    vl = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", name, "memory")
    pr = vl.dataProvider()
    for lbl, lon, lat in rows:
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        f.setAttributes([lbl])
        pr.addFeature(f)
    vl.updateExtents()
    vl.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": shape, "color": color, "size": str(size),
         "outline_color": "white", "outline_width": "0.4"})))
    s = QgsPalLayerSettings()
    s.fieldName = "label"
    s.placement = Qgis.LabelPlacement.OverPoint
    s.xOffset, s.yOffset = 3.2, -2.4
    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 10))
    tf.setSize(11)
    tf.setColor(QColor(labelcolor))
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.1)
    buf.setColor(QColor("white"))
    tf.setBuffer(buf)
    s.setFormat(tf)
    vl.setLabeling(QgsVectorLayerSimpleLabeling(s))
    vl.setLabelsEnabled(True)
    proj.addMapLayer(vl)
    return vl


def build_terrain(proj):
    processing.run("gdal:hillshade", {"INPUT": DEM, "BAND": 1, "Z_FACTOR": 1.6,
                                      "AZIMUTH": 315, "ALTITUDE": 45,
                                      "COMPUTE_EDGES": True, "OUTPUT": HS})
    hs = QgsRasterLayer(HS, "Hillshade")
    dem = QgsRasterLayer(DEM, "Elevation")
    proj.addMapLayer(hs)
    proj.addMapLayer(dem)

    ramp = QgsColorRampShader(0, 3150, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList(
        [QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v}") for v, c in HYPSO])
    sh = QgsRasterShader()
    sh.setRasterShaderFunction(ramp)
    dem.setRenderer(QgsSingleBandPseudoColorRenderer(dem.dataProvider(), 1, sh))
    dem.setBlendMode(QPainter.CompositionMode_SourceOver)
    hs.setBlendMode(QPainter.CompositionMode_Multiply)
    hs.setOpacity(0.42)
    return dem, hs


def main():
    proj = QgsProject.instance()
    proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    dem, hs = build_terrain(proj)

    res = QgsVectorLayer(GPKG + "|layername=water", "Al Massira reservoir", "ogr")
    res.setSubsetString("year=2017")
    res.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "26,107,143,255", "outline_color": "255,255,255,180", "outline_width": "0.3"})))
    proj.addMapLayer(res)
    dams = points(proj, "Dams & reservoirs", DAMS, "#b3261e", "triangle", 4.2, "#7a1c15")
    cities = points(proj, "Cities", CITIES, "#20140c", "circle", 2.6, "#20140c")

    order = [cities, dams, res, hs, dem]

    mgr = proj.layoutManager()
    for lay in mgr.printLayouts():
        mgr.removeLayout(lay)
    layout = QgsPrintLayout(proj)
    layout.initializeDefaults()
    layout.setName("WaterJourney")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM))
    mgr.addLayout(layout)

    def label(text, x, y, size, bold=False, color="#20140c", width=None, alpha=255):
        it = QgsLayoutItemLabel(layout)
        it.setText(text)
        f = QFont("Arial")
        f.setPointSizeF(float(size))
        f.setBold(bold)
        it.setFont(f)
        c = QColor(color)
        c.setAlpha(alpha)
        it.setFontColor(c)
        it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM))
        layout.addLayoutItem(it)
        return it

    xform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*EXTENT_LL))
    m = QgsLayoutItemMap(layout)
    m.attemptSetSceneRect(QRectF(8, 30, 292, 258))
    m.setLayers(order)
    m.setExtent(ext)
    m.setFrameEnabled(True)
    m.setFrameStrokeColor(QColor("#333333"))
    layout.addLayoutItem(m)

    label("The Water Journey", 8, 6, 30, bold=True, color="#5a3a1c")
    label("Where Morocco\u2019s water begins \u2014 Atlas snowmelt, the Oum Er-Rbia, and the Al Massira reservoir",
          9, 20, 13, color="#4a3320")
    label("M I D D L E   A T L A S", 150, 165, 17, bold=True, color="#4a3016", width=140, alpha=150)

    panel = QgsLayoutItemShape(layout)
    panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple(
        {"color": "252,250,245,255", "outline_color": "220,215,205,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)

    label("Morocco\u2019s water starts high.", 312, 36, 15, bold=True, color="#5a3a1c", width=97)
    label("Winter snow and rain on the Middle Atlas \u2014 the pale peaks, rising above 3,000 m \u2014 "
          "drain down the Oum Er-Rbia and collect behind the Al Massira Dam. From this one reservoir, "
          "water travels northwest to Casablanca and the Doukkala farmland.", 312, 47, 10.5, color="#3a2c1e", width=97)
    label("When the mountains get less snow, everything downstream feels it \u2014 and Al Massira has "
          "already lost about 91% of its water surface since 2017.", 312, 82, 10.5, color="#3a2c1e", width=97)

    leg = QgsLayoutItemLegend(layout)
    leg.setLinkedMap(m)
    leg.setTitle("Water features")
    leg.setAutoUpdateModel(False)
    root = leg.model().rootGroup()
    for node in list(root.children()):
        if node.name() in ("Elevation", "Hillshade"):
            root.removeChildNode(node)
    leg.attemptMove(QgsLayoutPoint(312, 108, MM))
    layout.addLayoutItem(leg)

    label("Elevation", 312, 150, 11, bold=True)
    y = 158
    for val, col in LEGEND_SWATCHES:
        sw = QgsLayoutItemShape(layout)
        sw.setShapeType(QgsLayoutItemShape.Rectangle)
        sw.attemptSetSceneRect(QRectF(312, y, 11, 6.4))
        sw.setSymbol(QgsFillSymbol.createSimple({"color": col, "outline_color": "#b8ad98", "outline_width": "0.2"}))
        layout.addLayoutItem(sw)
        label(f"{val:,} m", 325, y + 0.6, 9.5, color="#3a2c1e")
        y += 6.4

    sb = QgsLayoutItemScaleBar(layout)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setNumberOfSegments(4)
    sb.setNumberOfSegmentsLeft(0)
    sb.setUnitsPerSegment(10)
    sb.setFont(QFont("Arial", 9))
    sb.update()
    sb.attemptMove(QgsLayoutPoint(312, 272, MM))
    layout.addLayoutItem(sb)

    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(17, 17, MM))
    na.attemptMove(QgsLayoutPoint(389, 263, MM))
    layout.addLayoutItem(na)

    label("Terrain: Copernicus GLO-30 DEM (ESA / Copernicus). Shaded relief + hypsometric tint rendered in QGIS.  "
          "Reservoir extent from Sentinel-2. Cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#7a6f5f", width=300)

    from _locator import add_locator

    add_locator(proj, layout, m, REPO)


    exporter = QgsLayoutExporter(layout)
    s = QgsLayoutExporter.ImageExportSettings()
    s.dpi = 300
    exporter.exportToImage(REPO + "/figures/map_water_journey.png", s)
    ps = QgsLayoutExporter.PdfExportSettings()
    ps.dpi = 300
    exporter.exportToPdf(REPO + "/figures/map_water_journey.pdf", ps)
    proj.write(REPO + "/qgis/water_journey.qgz")
    print("exported The Water Journey map at 300 dpi")


if __name__ == "__main__" or True:
    main()

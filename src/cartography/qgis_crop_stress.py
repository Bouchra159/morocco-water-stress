"""
qgis_crop_stress.py  (run inside QGIS: Plugins -> Python Console)
Professional QGIS print layout of crop water stress on the Doukkala plain:
NDMI change 2024 -> 2026 over satellite imagery, with legend, scale bar,
north arrow and credits.

Needs data/geo/crop_stress_change.tif (run src/measure_crop_stress.py first).
Output: figures/map_qgis_crop_stress.png (300 dpi), qgis/crop_stress.qgz
"""
import os
import pathlib


def _repo_root():
    """Repo root, whether run as a script or pasted into the QGIS console."""
    try:
        return str(pathlib.Path(__file__).resolve().parents[2])
    except NameError:
        return os.environ.get("MOROCCO_REPO", os.getcwd())


import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent) if "__file__" in dir() else ".")
from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle, QgsColorRampShader,
    QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication, QgsFillSymbol,
)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = _repo_root()
TIF = REPO + "/data/geo/crop_stress_change.tif"
AOI = (-8.60, 32.40, -8.35, 32.62)
MM = QgsUnitTypes.LayoutMillimeters
STOPS = [(-0.30, "#8c510a"), (-0.15, "#d8b365"), (-0.03, "#f6e8c3"),
         (0.03, "#c7eae5"), (0.15, "#5ab4ac"), (0.30, "#01665e")]


def main():
    proj = QgsProject.instance()
    proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    sat = QgsRasterLayer(
        "type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=19&zmin=0", "Satellite", "wms")
    proj.addMapLayer(sat)

    r = QgsRasterLayer(TIF, "Crop moisture change 2024\u21922026 (NDMI)")
    ramp = QgsColorRampShader(-0.30, 0.30, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList(
        [QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v:+.2f}") for v, c in STOPS])
    sh = QgsRasterShader()
    sh.setRasterShaderFunction(ramp)
    r.setRenderer(QgsSingleBandPseudoColorRenderer(r.dataProvider(), 1, sh))
    r.setOpacity(0.82)
    proj.addMapLayer(r)

    pt = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", "Doukkala", "memory")
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-8.47, 32.51)))
    f.setAttributes(["Doukkala irrigated plain"])
    pt.dataProvider().addFeature(f)
    pt.updateExtents()
    pt.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "255,255,0,255", "outline_color": "0,0,0,255",
         "outline_width": "0.4", "size": "3"})))
    s = QgsPalLayerSettings()
    s.fieldName = "label"
    s.placement = Qgis.LabelPlacement.OverPoint
    s.yOffset = -3.0
    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 11))
    tf.setSize(12)
    tf.setColor(QColor("white"))
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.1)
    buf.setColor(QColor(30, 30, 30))
    tf.setBuffer(buf)
    s.setFormat(tf)
    pt.setLabeling(QgsVectorLayerSimpleLabeling(s))
    pt.setLabelsEnabled(True)
    proj.addMapLayer(pt)

    order = [pt, r, sat]
    xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*AOI))
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
    layout.setName("CropStress")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM))
    mgr.addLayout(layout)

    def label(text, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout)
        it.setText(text)
        fnt = QFont("Arial")
        fnt.setPointSizeF(float(size))
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
    m.setExtent(ext)
    m.setFrameEnabled(True)
    m.setFrameStrokeColor(QColor("#333333"))
    layout.addLayoutItem(m)

    label("Crop Water Stress & Recovery \u2014 the Doukkala Plain", 8, 6, 27, bold=True, color="#5a3a1c")
    label("Change in crop moisture (Sentinel-2 NDMI), 2024 drought \u2192 2026 recovery \u2014 the farmland Al Massira irrigates",
          9, 19, 12, color="#444444")

    panel = QgsLayoutItemShape(layout)
    panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple(
        {"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label("After years of drought, the Doukkala fields\u2014fed by the Al Massira reservoir\u2014were "
          "moisture-stressed. The exceptional 2025\u201326 rains that refilled the dam also brought the "
          "crops back: green shows where the fields recovered between 2024 and 2026.", 312, 38, 11, color="#333333", width=97)

    leg = QgsLayoutItemLegend(layout)
    leg.setLinkedMap(m)
    leg.setTitle("NDMI change")
    leg.setAutoUpdateModel(False)
    root = leg.model().rootGroup()
    for node in list(root.children()):
        if node.name() == "Satellite":
            root.removeChildNode(node)
    leg.attemptMove(QgsLayoutPoint(312, 85, MM))
    layout.addLayoutItem(leg)
    label("green = crops recovered / wetter\nbrown = drier / still stressed", 312, 150, 10, color="#555555", width=97)

    sb = QgsLayoutItemScaleBar(layout)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setNumberOfSegments(4)
    sb.setNumberOfSegmentsLeft(0)
    sb.setUnitsPerSegment(5)
    sb.setFont(QFont("Arial", 9))
    sb.update()
    sb.attemptMove(QgsLayoutPoint(312, 268, MM))
    layout.addLayoutItem(sb)

    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(18, 18, MM))
    na.attemptMove(QgsLayoutPoint(388, 260, MM))
    layout.addLayoutItem(na)
    label("NDMI = (NIR\u2212SWIR)/(NIR+SWIR) from Sentinel-2 (Copernicus). Basemap: Esri World Imagery. "
          "Cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777777", width=300)

    from _locator import add_locator

    add_locator(proj, layout, m, REPO)


    exporter = QgsLayoutExporter(layout)
    s = QgsLayoutExporter.ImageExportSettings()
    s.dpi = 300
    exporter.exportToImage(REPO + "/figures/map_qgis_crop_stress.png", s)
    proj.write(REPO + "/qgis/crop_stress.qgz")
    print("exported crop-stress QGIS map")


if __name__ == "__main__" or True:
    main()

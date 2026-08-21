"""
qgis_greenness.py  (run inside QGIS: Plugins -> Python Console)
Professional QGIS print layout of vegetation change (NDVI, 2018 -> 2026) on the
argan / Anti-Atlas slopes near Taroudant, over satellite imagery.
Needs data/geo/ndvi_change_argan.tif.

Output: figures/map_qgis_greenness.png (300 dpi), qgis/greenness.qgz
"""
import os
from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle, QgsColorRampShader,
    QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemScaleBar,
    QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes,
    QgsLayoutExporter, QgsApplication, QgsFillSymbol)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = "C:/Users/BOUCHRA/Projects/morocco-water-stress"
TIF = REPO + "/data/geo/ndvi_change_argan.tif"
AOI = (-8.65, 30.05, -8.35, 30.35)
MM = QgsUnitTypes.LayoutMillimeters
STOPS = [(-0.25, "#8c510a"), (-0.12, "#d8b365"), (-0.03, "#f6e8c3"),
         (0.03, "#c7eae5"), (0.12, "#5ab4ac"), (0.25, "#01665e")]


def main():
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))
    sat = QgsRasterLayer("type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=19&zmin=0", "Satellite", "wms")
    proj.addMapLayer(sat)
    r = QgsRasterLayer(TIF, "Vegetation change 2018\u21922026 (NDVI)")
    ramp = QgsColorRampShader(-0.25, 0.25, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v:+.2f}") for v, c in STOPS])
    sh = QgsRasterShader(); sh.setRasterShaderFunction(ramp)
    r.setRenderer(QgsSingleBandPseudoColorRenderer(r.dataProvider(), 1, sh)); r.setOpacity(0.85)
    proj.addMapLayer(r)

    pt = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", "Place", "memory")
    f = QgsFeature(); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-8.47, 30.17))); f.setAttributes(["Igherm"])
    pt.dataProvider().addFeature(f); pt.updateExtents()
    pt.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "255,255,0,255", "outline_color": "0,0,0,255", "outline_width": "0.4", "size": "3"})))
    s = QgsPalLayerSettings(); s.fieldName = "label"; s.placement = Qgis.LabelPlacement.OverPoint; s.yOffset = -3.0
    tf = QgsTextFormat(); tf.setFont(QFont("Arial", 11)); tf.setSize(12); tf.setColor(QColor("white"))
    bf = QgsTextBufferSettings(); bf.setEnabled(True); bf.setSize(1.1); bf.setColor(QColor(30, 30, 30)); tf.setBuffer(bf)
    s.setFormat(tf); pt.setLabeling(QgsVectorLayerSimpleLabeling(s)); pt.setLabelsEnabled(True)
    proj.addMapLayer(pt)

    order = [pt, r, sat]
    xform = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*AOI))
    canvas = iface.mapCanvas(); canvas.setLayers(order); canvas.setExtent(ext); canvas.refresh(); canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for l in mgr.printLayouts():
        mgr.removeLayout(l)
    layout = QgsPrintLayout(proj); layout.initializeDefaults(); layout.setName("Greenness")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM)); mgr.addLayout(layout)

    def label(t, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout); it.setText(t)
        fn = QFont("Arial"); fn.setPointSizeF(float(size)); fn.setBold(bold); it.setFont(fn)
        it.setFontColor(QColor(color)); it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM)); layout.addLayoutItem(it); return it

    m = QgsLayoutItemMap(layout); m.attemptSetSceneRect(QRectF(8, 30, 292, 258))
    m.setLayers(order); m.setExtent(ext); m.setFrameEnabled(True); m.setFrameStrokeColor(QColor("#333"))
    layout.addLayoutItem(m)
    label("A Landscape Losing Its Green", 8, 6, 26, bold=True, color="#5a3a1c")
    label("Change in vegetation (Sentinel-2 NDVI), 2018 \u2192 2026 \u2014 the argan slopes near Taroudant",
          9, 19, 12, color="#444")

    panel = QgsLayoutItemShape(layout); panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple({"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label("The argan woodland is the last defence against the desert here. Brown marks slopes that lost "
          "vegetation between 2018 and 2026; green marks recovery after the 2025\u201326 rains. Both are "
          "written into the same hills my family comes from.", 312, 38, 10.5, color="#333", width=97)
    label("Legend", 312, 74, 12, bold=True, color="#20140c")
    sw = QgsLayoutItemShape(layout); sw.setShapeType(QgsLayoutItemShape.Ellipse); sw.attemptSetSceneRect(QRectF(313, 83, 4, 4))
    sw.setSymbol(QgsFillSymbol.createSimple({"color": "255,255,0,255", "outline_color": "0,0,0,255", "outline_width": "0.3"}))
    layout.addLayoutItem(sw)
    label("Igherm (town in the AOI)", 320, 82.5, 10, color="#333")
    label("Vegetation change (NDVI)", 312, 92, 10.5, bold=True, color="#20140c")
    leg = [(0.25, "#01665e", "greener / recovered"), (0.12, "#5ab4ac", ""), (0.0, "#f6e8c3", "\u2248 no change"),
           (-0.12, "#d8b365", ""), (-0.25, "#8c510a", "browner / vegetation lost")]
    y = 100
    for val, col, note in leg:
        sq = QgsLayoutItemShape(layout); sq.setShapeType(QgsLayoutItemShape.Rectangle); sq.attemptSetSceneRect(QRectF(312, y, 10, 6))
        sq.setSymbol(QgsFillSymbol.createSimple({"color": col, "outline_color": "#c8c8c8", "outline_width": "0.2"}))
        layout.addLayoutItem(sq)
        label(f"{val:+.2f}   {note}", 325, y + 0.6, 9, color="#3a2c1e"); y += 6.4

    sb = QgsLayoutItemScaleBar(layout); sb.setStyle("Single Box"); sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers); sb.setUnitLabel("km")
    sb.setNumberOfSegments(4); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(2)
    sb.setFont(QFont("Arial", 9)); sb.update(); sb.attemptMove(QgsLayoutPoint(312, 168, MM))
    layout.addLayoutItem(sb)
    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM)); na.attemptMove(QgsLayoutPoint(390, 162, MM))
    layout.addLayoutItem(na)
    label("NDVI = (NIR\u2212Red)/(NIR+Red) from Sentinel-2 (Copernicus). Basemap: Esri World Imagery. "
          "Cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777", width=300)

    png = REPO + "/figures/map_qgis_greenness.png"
    exp = QgsLayoutExporter(layout); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 300
    print("export:", exp.exportToImage(png, st))
    proj.write(REPO + "/qgis/greenness.qgz")


main()

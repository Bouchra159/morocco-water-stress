"""
qgis_rainshadow.py  (run inside QGIS: Plugins -> Python Console)
"A Desert in Disguise" — the rain shadow of the High Atlas.

Inspired by National Geographic's "Precipitation Across Landscapes" and
"California: A Desert in Disguise" lessons: shaded-relief terrain + a real
precipitation surface (NASA POWER), the 250 mm "desert line", and windward /
leeward annotations showing why the leeward south (home) runs dry.

Needs data/dem/souss_dem.tif and data/geo/precip_rainshadow.tif
(run src/measure_rainshadow.py first).
Output: figures/map_qgis_rainshadow.png (300 dpi), qgis/rainshadow.qgz
"""
import os
import pathlib


def _repo_root():
    """Repo root, whether run as a script or pasted into the QGIS console."""
    try:
        return str(pathlib.Path(__file__).resolve().parents[1])
    except NameError:
        return os.environ.get("MOROCCO_REPO", os.getcwd())


from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsColorRampShader, QgsRasterShader,
    QgsSingleBandPseudoColorRenderer, QgsHillshadeRenderer, QgsMarkerSymbol, QgsSingleSymbolRenderer,
    QgsLineSymbol, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutItemPolyline,
    QgsLayoutPoint, QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication, QgsFillSymbol)
from qgis.PyQt.QtGui import QColor, QFont, QPainter, QPolygonF
from qgis.PyQt.QtCore import QRectF, QPointF
from qgis.utils import iface
import processing

REPO = _repo_root()
DEM = REPO + "/data/dem/souss_dem.tif"
PRECIP = REPO + "/data/geo/precip_rainshadow.tif"
MM = QgsUnitTypes.LayoutMillimeters
# precipitation ramp: brown = dry / desert, blue = wet   (mm/yr)
STOPS = [(210, "#8c510a"), (240, "#bf912f"), (250, "#e8d9a0"),
         (270, "#c7eae5"), (295, "#5ab4ac"), (320, "#1c6f8c")]
TOWNS = {"Taroudant \u2014 home (leeward, ~246 mm)": (-8.88, 30.47),
         "High Atlas (windward, ~300 mm)": (-8.30, 31.70)}


def main():
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    try:
        proj.setEllipsoid("EPSG:7030")           # WGS84 -> scale bar in km
    except Exception:
        pass

    hs = QgsRasterLayer(DEM, "Hillshade")
    hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315.0, 45.0))
    proj.addMapLayer(hs)

    pr = QgsRasterLayer(PRECIP, "Annual rainfall")
    ramp = QgsColorRampShader(210, 320, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v} mm") for v, c in STOPS])
    sh = QgsRasterShader(); sh.setRasterShaderFunction(ramp)
    pr.setRenderer(QgsSingleBandPseudoColorRenderer(pr.dataProvider(), 1, sh))
    pr.setOpacity(0.55)
    proj.addMapLayer(pr)

    # 250 mm "desert line" contour
    desert = None
    try:
        res = processing.run("gdal:contour", {"INPUT": PRECIP, "BAND": 1, "INTERVAL": 1000,
              "OFFSET": 250, "FIELD_NAME": "mm", "OUTPUT": "TEMPORARY_OUTPUT"})
        desert = QgsVectorLayer(res["OUTPUT"], "Desert line (250 mm/yr)", "ogr")
        if desert.isValid() and desert.featureCount() > 0:
            desert.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple(
                {"color": "178,24,43,255", "width": "0.8", "line_style": "dash"})))
            proj.addMapLayer(desert)
        else:
            desert = None
    except Exception as e:
        print("contour skipped:", e)

    pts = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(60)", "Places", "memory")
    for lab, (lon, lat) in TOWNS.items():
        f = QgsFeature(); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat))); f.setAttributes([lab])
        pts.dataProvider().addFeature(f)
    pts.updateExtents()
    pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "20,20,20,255", "outline_color": "255,255,255,255",
         "outline_width": "0.5", "size": "3"})))
    s = QgsPalLayerSettings(); s.fieldName = "label"; s.placement = Qgis.LabelPlacement.OverPoint; s.yOffset = -3.2
    tf = QgsTextFormat(); tf.setFont(QFont("Arial", 11)); tf.setSize(11); tf.setColor(QColor("white"))
    bf = QgsTextBufferSettings(); bf.setEnabled(True); bf.setSize(1.2); bf.setColor(QColor(30, 30, 30)); tf.setBuffer(bf)
    s.setFormat(tf); pts.setLabeling(QgsVectorLayerSimpleLabeling(s)); pts.setLabelsEnabled(True)
    proj.addMapLayer(pts)

    order = [pts] + ([desert] if desert else []) + [pr, hs]
    ext = pr.extent()                            # frame to the rainfall surface (seamless, no bare terrain edge)
    canvas = iface.mapCanvas(); canvas.setDestinationCrs(proj.crs())
    canvas.setLayers(order); canvas.setExtent(ext); canvas.refresh(); canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for l in mgr.printLayouts():
        mgr.removeLayout(l)
    layout = QgsPrintLayout(proj); layout.initializeDefaults(); layout.setName("RainShadow")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM)); mgr.addLayout(layout)

    def label(t, x, y, size, bold=False, color="#1a1a1a", width=None, italic=False):
        it = QgsLayoutItemLabel(layout); it.setText(t)
        fn = QFont("Arial"); fn.setPointSizeF(float(size)); fn.setBold(bold); fn.setItalic(italic); it.setFont(fn)
        it.setFontColor(QColor(color)); it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM)); layout.addLayoutItem(it); return it

    m = QgsLayoutItemMap(layout); m.attemptSetSceneRect(QRectF(8, 30, 292, 258))
    m.setLayers(order); m.setExtent(ext); m.setFrameEnabled(True); m.setFrameStrokeColor(QColor("#333"))
    layout.addLayoutItem(m)
    label("A Desert in Disguise", 8, 5, 27, bold=True, color="#6a4a24", width=220)
    label("The rain shadow of the High Atlas \u2014 why the leeward south, my home, runs dry (annual rainfall, NASA POWER)",
          9, 20, 12, color="#444", width=280)

    # ---- annotations over the map: windward / leeward + moisture arrow ----
    label("HIGH ATLAS \u2014 moist Atlantic air\nrises and rains out (windward)", 150, 42, 12, bold=True, color="#f5efe4", width=120)
    label("RAIN SHADOW \u2014 the dry,\nleeward south. Home.", 30, 235, 13, bold=True, color="#fff1e0", width=110)
    arrow = QgsLayoutItemPolyline(QPolygonF([QPointF(40, 120), QPointF(150, 70)]), layout)
    sym = QgsLineSymbol.createSimple({"color": "40,120,170,220", "width": "2.4"})
    arrow.setSymbol(sym)
    try:
        arrow.setEndMarker(QgsLayoutItemPolyline.ArrowHead)
        arrow.setArrowHeadWidth(6.0)
        arrow.setArrowHeadStrokeColor(QColor(40, 120, 170))
        arrow.setArrowHeadFillColor(QColor(40, 120, 170))
    except Exception as e:
        print("arrowhead skipped:", e)
    layout.addLayoutItem(arrow)
    label("Atlantic\nmoisture", 20, 108, 11, bold=True, color="#1c6f8c", width=40)

    # ---- info panel ----
    panel = QgsLayoutItemShape(layout); panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple({"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label("Mountains decide who gets the rain. Atlantic moisture climbs the High Atlas and falls as rain "
          "on the windward north. By the time the air crosses to the leeward south \u2014 the Souss and "
          "Anti-Atlas, where I am from \u2014 it is wrung dry. The dashed line marks 250 mm/yr, the threshold "
          "geographers use to define a desert. My home sits right on it.", 312, 38, 10.5, color="#333", width=97)
    label("Annual rainfall", 312, 92, 11, bold=True, color="#20140c")
    y = 102
    for v, c in STOPS:
        sq = QgsLayoutItemShape(layout); sq.setShapeType(QgsLayoutItemShape.Rectangle); sq.attemptSetSceneRect(QRectF(312, y, 10, 6))
        sq.setSymbol(QgsFillSymbol.createSimple({"color": c, "outline_color": "#c8c8c8", "outline_width": "0.2"}))
        layout.addLayoutItem(sq)
        label(f"{v} mm/yr" + ("   \u2190 desert line" if v == 250 else ""), 325, y + 0.6, 9, color="#3a2c1e", width=80); y += 6.6
    ln = QgsLayoutItemShape(layout); ln.setShapeType(QgsLayoutItemShape.Rectangle); ln.attemptSetSceneRect(QRectF(312, y + 3, 10, 1.4))
    ln.setSymbol(QgsFillSymbol.createSimple({"color": "178,24,43,255", "outline_color": "178,24,43,255", "outline_width": "0"}))
    layout.addLayoutItem(ln)
    label("250 mm \u2014 the desert threshold", 325, y + 1.4, 9, color="#3a2c1e", width=80)

    sb = QgsLayoutItemScaleBar(layout); sb.setStyle("Single Box"); sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers); sb.setUnitLabel("km")
    sb.setNumberOfSegments(4); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(10)
    sb.setFont(QFont("Arial", 9)); sb.update(); sb.attemptMove(QgsLayoutPoint(312, 205, MM))
    layout.addLayoutItem(sb)
    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM)); na.attemptMove(QgsLayoutPoint(390, 199, MM))
    layout.addLayoutItem(na)
    label("Rainfall: NASA POWER climatology (annual), sampled on a grid and interpolated \u2014 coarse (~50 km), "
          "so the true mountain contrast is sharper. Terrain: Copernicus GLO-30 DEM. Cartography: B. Daddaoui, 2026.",
          8, 291, 7, color="#777", width=300)

    png = REPO + "/figures/map_qgis_rainshadow.png"
    exp = QgsLayoutExporter(layout); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 300
    print("export:", exp.exportToImage(png, st))
    proj.write(REPO + "/qgis/rainshadow.qgz")


main()

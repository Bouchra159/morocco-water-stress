"""
qgis_argan_terrain.py  (run inside QGIS: Plugins -> Python Console)
Professional QGIS shaded-relief map of the author's home region: the Souss valley
and Anti-Atlas argan belt. Hypsometric tint + hillshade from data/dem/souss_dem.tif.

Output: figures/map_qgis_argan_terrain.png (300 dpi), qgis/argan_terrain.qgz
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
    QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsHillshadeRenderer, QgsMarkerSymbol,
    QgsSingleSymbolRenderer, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication, QgsFillSymbol, QgsProperty)
from qgis.PyQt.QtGui import QColor, QFont, QPainter
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = _repo_root()
DEM = REPO + "/data/dem/souss_dem.tif"
MM = QgsUnitTypes.LayoutMillimeters
HYPSO = [(0, "#e8e0c8"), (600, "#d8b98a"), (1200, "#b3895a"),
         (1800, "#8a6a45"), (2500, "#9a8a7a"), (3100, "#e2ded6"), (3580, "#ffffff")]
TOWNS = {"Agadir": (-9.58, 30.42), "Taroudant": (-8.88, 30.47), "Oulad Teima": (-9.21, 30.39),
         "Aoulouz": (-8.16, 30.68), "Igherm": (-8.47, 30.09), "Ait Baha": (-9.15, 30.07)}
REGIONS = {"H I G H   A T L A S": (-8.70, 31.00), "S O U S S   V A L L E Y": (-9.00, 30.42),
           "A N T I - A T L A S": (-8.70, 30.15)}


def main():
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    tint = QgsRasterLayer(DEM, "Elevation")
    ramp = QgsColorRampShader(0, 3580, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v} m") for v, c in HYPSO])
    sh = QgsRasterShader(); sh.setRasterShaderFunction(ramp)
    tint.setRenderer(QgsSingleBandPseudoColorRenderer(tint.dataProvider(), 1, sh))
    proj.addMapLayer(tint)

    hs = QgsRasterLayer(DEM, "Hillshade")
    hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315.0, 45.0))
    hs.setBlendMode(QPainter.CompositionMode_Multiply)
    hs.setOpacity(0.65)
    proj.addMapLayer(hs)

    def point_layer(name, coords, marker, tsize, italic=False, offset=-3.0):
        v = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", name, "memory")
        for lab, (lon, lat) in coords.items():
            f = QgsFeature(); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat))); f.setAttributes([lab])
            v.dataProvider().addFeature(f)
        v.updateExtents()
        if marker:
            v.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
                {"name": "circle", "color": "30,30,30,255", "outline_color": "255,255,255,255",
                 "outline_width": "0.4", "size": "2.4"})))
        else:
            v.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
                {"name": "circle", "color": "0,0,0,0", "outline_color": "0,0,0,0", "size": "0.1"})))
        s = QgsPalLayerSettings(); s.fieldName = "label"; s.placement = Qgis.LabelPlacement.OverPoint
        s.yOffset = offset
        s.priority = 10 if italic else 5          # region names win placement
        try:
            s.obstacleSettings().setIsObstacle(False)
        except Exception:
            pass
        tf = QgsTextFormat(); fnt = QFont("Arial", 11); fnt.setItalic(italic); fnt.setBold(italic)
        tf.setFont(fnt); tf.setSize(tsize)
        tf.setColor(QColor("#f5efe4" if italic else "white"))
        bf = QgsTextBufferSettings(); bf.setEnabled(True); bf.setSize(1.4 if italic else 1.0)
        bf.setColor(QColor(60, 45, 30) if italic else QColor(40, 40, 40))
        tf.setBuffer(bf); s.setFormat(tf)
        v.setLabeling(QgsVectorLayerSimpleLabeling(s)); v.setLabelsEnabled(True)
        proj.addMapLayer(v); return v

    regions = point_layer("Regions", REGIONS, False, 13, italic=True, offset=0.0)
    towns = point_layer("Towns", TOWNS, True, 11, italic=False, offset=-3.0)

    order = [towns, regions, hs, tint]
    ext = QgsCoordinateTransform(QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj).transformBoundingBox(tint.extent()) \
        if tint.crs().authid() != "EPSG:3857" else tint.extent()
    # DEM is EPSG:4326; transform its extent
    ext = QgsCoordinateTransform(tint.crs(), proj.crs(), proj).transformBoundingBox(tint.extent())
    canvas = iface.mapCanvas(); canvas.setLayers(order); canvas.setExtent(ext); canvas.refresh(); canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for l in mgr.printLayouts():
        mgr.removeLayout(l)
    layout = QgsPrintLayout(proj); layout.initializeDefaults(); layout.setName("ArganTerrain")
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
    label("Argan Country", 8, 5, 26, bold=True, color="#6a4a24", width=200)
    label("Where I'm from \u2014 the Souss valley and the Anti-Atlas of southern Morocco (Copernicus GLO-30 DEM)",
          9, 20, 12, color="#444", width=270)

    panel = QgsLayoutItemShape(layout); panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple({"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label("The argan tree grows almost nowhere else on Earth. It holds these slopes between the High "
          "Atlas and the Anti-Atlas together, in one of the most water-stressed corners of Morocco. "
          "This is home.", 312, 38, 10.5, color="#333", width=97)
    label("Elevation", 312, 76, 11, bold=True, color="#20140c")
    y = 86
    for v, c in HYPSO:
        sq = QgsLayoutItemShape(layout); sq.setShapeType(QgsLayoutItemShape.Rectangle); sq.attemptSetSceneRect(QRectF(312, y, 10, 6))
        sq.setSymbol(QgsFillSymbol.createSimple({"color": c, "outline_color": "#c8c8c8", "outline_width": "0.2"}))
        layout.addLayoutItem(sq)
        label(f"{v:,} m", 325, y + 1.0, 9, color="#3a2c1e", width=45); y += 6.6

    sb = QgsLayoutItemScaleBar(layout); sb.setStyle("Single Box"); sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers); sb.setUnitLabel("km")
    sb.setNumberOfSegments(4); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(10)
    sb.setFont(QFont("Arial", 9)); sb.update(); sb.attemptMove(QgsLayoutPoint(312, 200, MM))
    layout.addLayoutItem(sb)
    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM)); na.attemptMove(QgsLayoutPoint(390, 194, MM))
    layout.addLayoutItem(na)
    label("Terrain: Copernicus GLO-30 DEM (ESA / Copernicus). Shaded relief + hypsometric tint. "
          "Cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777", width=300)

    png = REPO + "/figures/map_qgis_argan_terrain.png"
    from _locator import add_locator
    add_locator(proj, layout, m, REPO)

    exp = QgsLayoutExporter(layout); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 300
    print("export:", exp.exportToImage(png, st))
    proj.write(REPO + "/qgis/argan_terrain.qgz")


main()

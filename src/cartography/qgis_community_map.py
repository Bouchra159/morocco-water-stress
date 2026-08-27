"""
qgis_community_map.py
"Who Depends on Al Massira?" — a community-conservation map connecting the
reservoir's collapse to the people and farmland that rely on it.

Runs inside QGIS (Python Console). Tested on QGIS 3.40. Needs:
  data/geo/morocco_adm1.geojson          (run src/fetch_geodata.py)
  data/geo/al_massira_water.gpkg         (run src/export_reservoir_vectors.py)
  data/raw/communities_al_massira.csv    (community figures + sources)

Outputs: figures/map_communities_al_massira.png (300 dpi) + .pdf,
         qgis/al_massira_communities.qgz
"""

import os
import pathlib


def _repo_root():
    """Repo root, whether run as a script or pasted into the QGIS console."""
    try:
        return str(pathlib.Path(__file__).resolve().parents[2])
    except NameError:
        return os.environ.get("MOROCCO_REPO", os.getcwd())


import csv
from qgis.core import (
    Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle,
    QgsFillSymbol, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsProperty, QgsSymbolLayer,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
    QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel, QgsLayoutItemLegend,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication,
)
from qgis.PyQt.QtGui import QFont, QColor
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = _repo_root()
GEO = REPO + "/data/geo/"
GPKG = GEO + "al_massira_water.gpkg"
CSV = REPO + "/data/raw/communities_al_massira.csv"
MM = QgsUnitTypes.LayoutMillimeters
EXTENT_LL = (-9.55, 31.95, -6.25, 34.05)


def read_cities():
    rows = []
    with open(CSV, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or line.startswith("name,"):
                continue
            n, lon, lat, pop, _role = line.strip().split(",", 4)
            rows.append((n, float(lon), float(lat), int(pop)))
    return rows


def build_layers():
    proj = QgsProject.instance()
    proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    base = QgsRasterLayer(
        "type=xyz&url=https://a.basemaps.cartocdn.com/light_all/%7Bz%7D/%7Bx%7D/%7By%7D.png&zmax=19&zmin=0",
        "CARTO Light", "wms")
    proj.addMapLayer(base)

    reg = QgsVectorLayer(GEO + "morocco_adm1.geojson", "Casablanca-Settat region", "ogr")
    reg.setSubsetString("\"shapeName\" = 'Casablanca-Settat'")
    reg.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "42,111,151,35", "outline_color": "42,111,151,220", "outline_width": "0.6"})))
    proj.addMapLayer(reg)

    w2017 = QgsVectorLayer(GPKG + "|layername=water", "Al Massira 2017", "ogr")
    w2017.setSubsetString("year=2017")
    w2017.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "0,150,200,255", "outline_width": "0.5"})))
    proj.addMapLayer(w2017)

    w2024 = QgsVectorLayer(GPKG + "|layername=water", "Al Massira 2024", "ogr")
    w2024.setSubsetString("year=2024")
    w2024.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "179,38,30,255", "outline_color": "white", "outline_width": "0.2"})))
    proj.addMapLayer(w2024)

    douk = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(60)", "Doukkala irrigated plain", "memory")
    f = QgsFeature()
    f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(-8.35, 32.75)))
    f.setAttributes(["Doukkala irrigated plain"])
    douk.dataProvider().addFeature(f)
    douk.updateExtents()
    douk.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "120,180,90,90", "outline_color": "90,150,60,255",
         "outline_width": "0.5", "size": "14"})))
    proj.addMapLayer(douk)

    city = QgsVectorLayer("Point?crs=EPSG:4326&field=name:string(30)&field=pop:integer", "Communities", "memory")
    pr = city.dataProvider()
    for n, lon, lat, pop in read_cities():
        ft = QgsFeature()
        ft.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        ft.setAttributes([n, pop])
        pr.addFeature(ft)
    city.updateExtents()
    csym = QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "26,26,26,255", "outline_color": "white", "outline_width": "0.5"})
    csym.symbolLayer(0).setDataDefinedProperty(
        QgsSymbolLayer.PropertySize, QgsProperty.fromExpression('2 + sqrt("pop")/450'))
    city.setRenderer(QgsSingleSymbolRenderer(csym))
    s = QgsPalLayerSettings()
    s.fieldName = "name"
    s.placement = Qgis.LabelPlacement.OverPoint
    s.xOffset, s.yOffset = 3.5, -2.5
    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 10))
    tf.setSize(11)
    tf.setColor(QColor(20, 20, 20))
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.0)
    buf.setColor(QColor("white"))
    tf.setBuffer(buf)
    s.setFormat(tf)
    city.setLabeling(QgsVectorLayerSimpleLabeling(s))
    city.setLabelsEnabled(True)
    proj.addMapLayer(city)

    order = [city, w2024, w2017, douk, reg, base]
    return proj, order


def build_layout(proj, order):
    xform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    ext = xform.transformBoundingBox(QgsRectangle(*EXTENT_LL))
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
    layout.setName("Community")
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM))
    mgr.addLayout(layout)

    def label(text, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout)
        it.setText(text)
        f = QFont("Arial")
        f.setPointSizeF(float(size))
        f.setBold(bold)
        it.setFont(f)
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
    m.setBackgroundColor(QColor(235, 241, 245))
    m.setExtent(ext)
    m.setFrameEnabled(True)
    m.setFrameStrokeColor(QColor("#333333"))
    layout.addLayoutItem(m)

    label("Who Depends on Al Massira?", 8, 6, 30, bold=True, color="#0d3b5c")
    label("The communities living on a vanishing reservoir — Oum Er-Rbia basin, Morocco",
          9, 20, 13, color="#444444")
    label("Al Massira reservoir\n(−91% water since 2017)", 120, 176, 11, bold=True, color="#b3261e", width=58)

    panel = QgsLayoutItemShape(layout)
    panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 30, 107, 258))
    panel.setSymbol(QgsFillSymbol.createSimple(
        {"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)

    label("7.7 million", 312, 36, 30, bold=True, color="#2a6f97")
    label("people in the Casablanca-Settat region\n(2024 census) rely on this basin", 312, 52, 10.5, color="#333333", width=97)
    label("96,000 ha", 312, 74, 30, bold=True, color="#5a9a3c")
    label("of Doukkala farmland irrigated from\nthe Oum Er-Rbia / Al Massira system", 312, 90, 10.5, color="#333333", width=97)
    label("−91%", 312, 112, 30, bold=True, color="#b3261e")
    label("of the reservoir's water surface lost\nbetween 2017 and 2024", 312, 128, 10.5, color="#333333", width=97)
    label("Al Massira is also a Ramsar site — a\nwetland of international importance for\nbirds and biodiversity, now shrinking.",
          312, 152, 10, color="#555555", width=97)

    leg = QgsLayoutItemLegend(layout)
    leg.setLinkedMap(m)
    leg.setTitle("Legend")
    leg.setAutoUpdateModel(False)
    root = leg.model().rootGroup()
    for node in list(root.children()):
        if node.name() == "CARTO Light":
            root.removeChildNode(node)
    leg.attemptMove(QgsLayoutPoint(312, 185, MM))
    layout.addLayoutItem(leg)

    sb = QgsLayoutItemScaleBar(layout)
    sb.setStyle("Single Box")
    sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers)
    sb.setUnitLabel("km")
    sb.setNumberOfSegments(4)
    sb.setNumberOfSegmentsLeft(0)
    sb.setUnitsPerSegment(20)
    sb.setFont(QFont("Arial", 9))
    sb.update()
    sb.attemptMove(QgsLayoutPoint(312, 270, MM))
    layout.addLayoutItem(sb)

    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(18, 18, MM))
    na.attemptMove(QgsLayoutPoint(388, 262, MM))
    layout.addLayoutItem(na)

    label("Region population: HCP Morocco 2024 census. City sizes: 2014 census. Irrigation: ORMVAD (Doukkala).  "
          "Reservoir extents measured from Sentinel-2 (NDWI+Otsu). Basemap: CARTO / OpenStreetMap.  "
          "Analysis & cartography: B. Daddaoui, 2026.", 8, 291, 7, color="#777777", width=300)

    exporter = QgsLayoutExporter(layout)
    s = QgsLayoutExporter.ImageExportSettings()
    s.dpi = 300
    exporter.exportToImage(REPO + "/figures/map_communities_al_massira.png", s)
    ps = QgsLayoutExporter.PdfExportSettings()
    ps.dpi = 300
    exporter.exportToPdf(REPO + "/figures/map_communities_al_massira.pdf", ps)
    proj.write(REPO + "/qgis/al_massira_communities.qgz")
    print("exported community map at 300 dpi")


if __name__ == "__main__" or True:
    _proj, _order = build_layers()
    build_layout(_proj, _order)

"""
qgis_basin_map.py
Reproducible PyQGIS script that builds the terrain basin map (fig: qgis_basin_map.png).

HOW TO RUN
----------
This uses the QGIS Python API (PyQGIS), so it runs *inside* QGIS, not the plain
Python venv. Open QGIS -> Plugins -> Python Console -> Show Editor, load this
file and Run; or paste it into the console. Tested on QGIS 3.40.

It uses only public open data:
  - OpenTopoMap terrain tiles (CC-BY-SA) as the basemap
  - geoBoundaries Morocco ADM0/ADM1 (CC BY 4.0)  -> run src/fetch_geodata.py first
  - well-known public coordinates for the dams and cities

The map centres on the Oum Er-Rbia system: Atlas snowmelt feeds the Al Massira
reservoir, which supplies Casablanca and the Doukkala irrigated plain.
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
    Qgis, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsRectangle, QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsFillSymbol, QgsMarkerSymbol, QgsRuleBasedRenderer, QgsSingleSymbolRenderer,
    QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsMapSettings, QgsMapRendererParallelJob,
)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QFont

REPO = _repo_root()
GEO = REPO + "/data/geo/"
OUT = REPO + "/figures/qgis_basin_map.png"

BASIN_REGIONS = ("Béni Mellal-Khénifra", "Casablanca-Settat")
DAMS = {"Al Massira Dam": (-7.62, 32.53), "Bin el Ouidane Dam": (-6.44, 32.10)}
CITIES = {"Casablanca": (-7.59, 33.57), "Beni Mellal": (-6.36, 32.34)}


def add_points(proj, name, pts, color, shape, size):
    vl = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", name, "memory")
    pr = vl.dataProvider()
    for label, (lon, lat) in pts.items():
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat)))
        f.setAttributes([label])
        pr.addFeature(f)
    vl.updateExtents()
    vl.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": shape, "color": color, "size": str(size),
         "outline_color": "white", "outline_width": "0.4"})))
    s = QgsPalLayerSettings()
    s.fieldName = "label"
    s.placement = Qgis.LabelPlacement.OverPoint
    s.xOffset, s.yOffset = 3.0, -2.2
    tf = QgsTextFormat()
    tf.setFont(QFont("Arial", 9))
    tf.setSize(10)
    tf.setColor(QColor(color) if shape == "triangle" else QColor(30, 30, 30))
    buf = QgsTextBufferSettings()
    buf.setEnabled(True)
    buf.setSize(1.0)
    buf.setColor(QColor("white"))
    tf.setBuffer(buf)
    s.setFormat(tf)
    vl.setLabeling(QgsVectorLayerSimpleLabeling(s))
    vl.setLabelsEnabled(True)
    proj.addMapLayer(vl)
    return vl


def main():
    proj = QgsProject.instance()
    proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:3857"))

    topo = QgsRasterLayer(
        "type=xyz&url=https://a.tile.opentopomap.org/{z}/{x}/{y}.png&zmax=17&zmin=0",
        "OpenTopoMap", "wms")
    proj.addMapLayer(topo)

    adm0 = QgsVectorLayer(GEO + "morocco_adm0.geojson", "Morocco", "ogr")
    adm1 = QgsVectorLayer(GEO + "morocco_adm1.geojson", "Regions", "ogr")
    proj.addMapLayer(adm1)
    proj.addMapLayer(adm0)

    # rule-based highlight of the two Oum Er-Rbia core regions
    base_sym = QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "150,150,150,120", "outline_width": "0.3"})
    root = QgsRuleBasedRenderer(base_sym.clone())
    rule_root = root.rootRule()
    basin = rule_root.children()[0].clone()
    names = "','".join(BASIN_REGIONS)
    basin.setFilterExpression(f"\"shapeName\" IN ('{names}')")
    basin.setLabel("Oum Er-Rbia core regions")
    basin.setSymbol(QgsFillSymbol.createSimple(
        {"color": "224,122,31,70", "outline_color": "224,122,31,255", "outline_width": "0.9"}))
    rule_root.appendChild(basin)
    other = rule_root.children()[0].clone()
    other.setFilterExpression("ELSE")
    other.setLabel("Other regions")
    other.setSymbol(base_sym.clone())
    rule_root.appendChild(other)
    rule_root.removeChildAt(0)
    adm1.setRenderer(root)

    adm0.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"color": "0,0,0,0", "outline_color": "50,50,50,255", "outline_width": "0.5"})))

    cities = add_points(proj, "Cities", CITIES, "#1a1a1a", "circle", 2.6)
    dams = add_points(proj, "Dams", DAMS, "#b3261e", "triangle", 5.0)

    order = [cities, dams, adm1, adm0, topo]

    xform = QgsCoordinateTransform(
        QgsCoordinateReferenceSystem("EPSG:4326"), proj.crs(), proj)
    rect = xform.transformBoundingBox(QgsRectangle(-10.2, 31.0, -4.3, 34.4))

    ms = QgsMapSettings()
    ms.setLayers(order)
    ms.setDestinationCrs(proj.crs())
    ms.setExtent(rect)
    ms.setOutputSize(QSize(1400, 1000))
    ms.setBackgroundColor(QColor(255, 255, 255))
    ms.setOutputDpi(150)
    job = QgsMapRendererParallelJob(ms)
    job.start()
    job.waitForFinished()
    ok = job.renderedImage().save(OUT)
    print("saved", OUT, ok)


if __name__ == "__main__" or True:  # also runs when pasted into the QGIS console
    main()

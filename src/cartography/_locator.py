"""
_locator.py
A small locator inset for the QGIS print layouts.

Every map of a small area needs one. A reader looking at "the Doukkala plain" or
"the Souss valley" has no way of knowing where that is unless the map shows it.
It is one of the standard map elements, along with the title, legend, scale bar
and north arrow.

This draws Morocco with a red rectangle around whatever the main map is showing.
QGIS keeps the rectangle in sync with the main map on its own, through the
overview frame, so it stays correct if the extent ever changes.

Usage, from inside a layout script:

    from _locator import add_locator
    add_locator(proj, layout, m, REPO)
"""
from qgis.core import (
    QgsVectorLayer, QgsFillSymbol, QgsSingleSymbolRenderer, QgsLayoutItemMap,
    QgsLayoutItemLabel, QgsLayoutItemMapOverview, QgsLayoutPoint, QgsLayoutSize,
    QgsUnitTypes, QgsCoordinateTransform)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtCore import QRectF

MM = QgsUnitTypes.LayoutMillimeters
LAND = "232,226,212,255"
COAST = "120,110,95,255"
SEA = QColor(214, 229, 238)
BOX = "200,30,30,255"


def add_locator(proj, layout, main_map, repo, x=8.0, y=32.0, size=46.0,
                caption="study area"):
    """Add a Morocco locator inset showing the extent of `main_map`.

    Fails quietly: a missing outline should never stop a map from exporting.
    """
    try:
        outline = QgsVectorLayer(repo + "/data/geo/morocco_adm0.geojson", "Morocco", "ogr")
        if not outline.isValid():
            print("  locator: morocco outline not found, skipping")
            return None

        outline.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
            {"color": LAND, "outline_color": COAST, "outline_width": "0.25"})))
        proj.addMapLayer(outline, False)          # in the project, not the legend

        inset = QgsLayoutItemMap(layout)
        inset.attemptSetSceneRect(QRectF(x, y, size, size))
        inset.setLayers([outline])
        # the outline is in EPSG:4326; the layout may be in Web Mercator, so put
        # the extent into whatever CRS the project is actually using
        extent = outline.extent()
        if outline.crs() != proj.crs():
            extent = QgsCoordinateTransform(
                outline.crs(), proj.crs(), proj).transformBoundingBox(extent)
            extent.grow(max(extent.width(), extent.height()) * 0.05)
        else:
            extent.grow(0.6)                       # degrees: a little sea around it
        inset.setExtent(extent)
        inset.setBackgroundColor(SEA)
        inset.setFrameEnabled(True)
        inset.setFrameStrokeColor(QColor("#555555"))
        layout.addLayoutItem(inset)

        # QGIS draws the main map's extent onto the inset and keeps it in sync
        ov = QgsLayoutItemMapOverview("aoi", inset)
        ov.setLinkedMap(main_map)
        ov.setFrameSymbol(QgsFillSymbol.createSimple(
            {"color": "0,0,0,0", "outline_color": BOX, "outline_width": "0.9"}))
        inset.overviews().addOverview(ov)
        inset.refresh()

        if caption:
            lab = QgsLayoutItemLabel(layout)
            lab.setText(caption)
            fnt = QFont("Arial")
            fnt.setPointSizeF(7.5)
            fnt.setBold(True)
            lab.setFont(fnt)
            lab.setFontColor(QColor("#333333"))
            lab.adjustSizeToText()
            lab.attemptResize(QgsLayoutSize(size, 4.0, MM))
            lab.attemptMove(QgsLayoutPoint(x + 2, y + size + 0.5, MM))
            layout.addLayoutItem(lab)
        return inset
    except Exception as e:
        print("  locator inset skipped:", e)
        return None

"""
qgis_souss_triptych.py  (run inside QGIS: Plugins -> Python Console)
"A Desert in Disguise: Souss-Massa" — the three-map story, after National
Geographic's California lesson (SUPPLY / DELIVERY / USE) plus a fourth "untold"
panel.

  1 SUPPLY   — where the rain falls (rain shadow of the High Atlas)
  2 DELIVERY — the terrain and rivers that carry what little there is
  3 USE      — the irrigated export farmland glowing in a semi-arid plain
  4 COST     — what a rainfall control reveals about that green

Run one panel at a time: main("supply") / main("delivery") / main("use"), or
main("all") for the three, then cost() for the fourth "untold" panel.

Outputs: figures/map_souss_supply.png, _delivery.png, _use.png, _cost.png (300 dpi)
"""
import os
from qgis.core import (
    Qgis, QgsProject, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsRectangle, QgsColorRampShader,
    QgsRasterShader, QgsSingleBandPseudoColorRenderer, QgsHillshadeRenderer,
    QgsPalettedRasterRenderer, QgsMarkerSymbol, QgsSingleSymbolRenderer, QgsLineSymbol,
    QgsFillSymbol, QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings,
    QgsVectorLayerSimpleLabeling, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemLabel,
    QgsLayoutItemScaleBar, QgsLayoutItemPicture, QgsLayoutItemShape, QgsLayoutPoint,
    QgsLayoutSize, QgsUnitTypes, QgsLayoutExporter, QgsApplication)
from qgis.PyQt.QtGui import QColor, QFont, QPainter
from qgis.PyQt.QtCore import QRectF
from qgis.utils import iface

REPO = "C:/Users/BOUCHRA/Projects/morocco-water-stress"
DEM = REPO + "/data/dem/souss_massa_dem.tif"
PRECIP = REPO + "/data/geo/precip_souss_massa.tif"
NDVI = REPO + "/data/geo/souss_ndvi.tif"
REGION = REPO + "/data/geo/souss_massa.gpkg"
MM = QgsUnitTypes.LayoutMillimeters
REGION_EXT = QgsRectangle(-9.95, 28.4, -6.45, 31.15)
PLAIN_EXT = QgsRectangle(-9.60, 30.15, -8.55, 30.75)

PRECIP_STOPS = [(60, "#8c510a"), (110, "#bf912f"), (170, "#e8d9a0"),
                (250, "#e8e8c8"), (300, "#5ab4ac"), (360, "#1c6f8c")]
ELEV_STOPS = [(0, "#e8e0c8"), (600, "#d8b98a"), (1200, "#b3895a"),
              (2000, "#8a6a45"), (3000, "#9a8a7a"), (4100, "#ffffff")]
TOWNS = {"Agadir": (-9.58, 30.42), "Taroudant": (-8.88, 30.47), "Oulad Teima": (-9.21, 30.39),
         "Tiznit": (-9.73, 29.70), "Taliouine": (-7.93, 30.53), "Tata": (-7.97, 29.75)}


def _base(name):
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    try:
        proj.setEllipsoid("EPSG:7030")
    except Exception:
        pass
    return proj


def _hillshade(path=DEM, opacity=1.0, blend=False):
    hs = QgsRasterLayer(path, "Hillshade")
    hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315.0, 45.0))
    hs.setOpacity(opacity)
    if blend:
        hs.setBlendMode(QPainter.CompositionMode_Multiply)
    return hs


def _pseudocolor(path, name, stops, lo, hi, opacity=1.0, fmt="{v:.0f}"):
    r = QgsRasterLayer(path, name)
    ramp = QgsColorRampShader(lo, hi, None, QgsColorRampShader.Interpolated)
    ramp.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), fmt.format(v=v))
                               for v, c in stops])
    sh = QgsRasterShader(); sh.setRasterShaderFunction(ramp)
    r.setRenderer(QgsSingleBandPseudoColorRenderer(r.dataProvider(), 1, sh))
    r.setOpacity(opacity)
    return r


def _region_outline(proj):
    v = QgsVectorLayer(REGION + "|layername=region", "Souss-Massa region", "ogr")
    if v.isValid():
        v.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
            {"color": "0,0,0,0", "outline_color": "40,40,40,200", "outline_width": "0.7",
             "outline_style": "dash"})))
        proj.addMapLayer(v)
        return v
    return None


def _towns(proj, subset=None, size="3"):
    pts = QgsVectorLayer("Point?crs=EPSG:4326&field=label:string(40)", "Towns", "memory")
    for lab, (lon, lat) in TOWNS.items():
        if subset and lab not in subset:
            continue
        f = QgsFeature(); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(lon, lat))); f.setAttributes([lab])
        pts.dataProvider().addFeature(f)
    pts.updateExtents()
    pts.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": "20,20,20,255", "outline_color": "255,255,255,255",
         "outline_width": "0.5", "size": size})))
    s = QgsPalLayerSettings(); s.fieldName = "label"
    s.placement = Qgis.LabelPlacement.OverPoint; s.yOffset = -3.2
    tf = QgsTextFormat(); tf.setFont(QFont("Arial", 11)); tf.setSize(11); tf.setColor(QColor("white"))
    bf = QgsTextBufferSettings(); bf.setEnabled(True); bf.setSize(1.2); bf.setColor(QColor(30, 30, 30))
    tf.setBuffer(bf); s.setFormat(tf)
    pts.setLabeling(QgsVectorLayerSimpleLabeling(s)); pts.setLabelsEnabled(True)
    proj.addMapLayer(pts)
    return pts


def _layout(proj, order, ext, title, subtitle, body, legend, note, out_png,
            eyebrow, seg_km, annotations=(), map_h=256):
    canvas = iface.mapCanvas(); canvas.setDestinationCrs(proj.crs())
    canvas.setLayers(order); canvas.setExtent(ext); canvas.refresh(); canvas.waitWhileRendering()

    mgr = proj.layoutManager()
    for l in mgr.printLayouts():
        mgr.removeLayout(l)
    layout = QgsPrintLayout(proj); layout.initializeDefaults(); layout.setName(title[:20])
    layout.pageCollection().pages()[0].setPageSize(QgsLayoutSize(420, 297, MM)); mgr.addLayout(layout)

    def label(t, x, y, size, bold=False, color="#1a1a1a", width=None):
        it = QgsLayoutItemLabel(layout); it.setText(t)
        fn = QFont("Arial"); fn.setPointSizeF(float(size)); fn.setBold(bold); it.setFont(fn)
        it.setFontColor(QColor(color)); it.adjustSizeToText()
        if width:
            it.attemptResize(QgsLayoutSize(width, it.sizeWithUnits().height(), MM))
        it.attemptMove(QgsLayoutPoint(x, y, MM)); layout.addLayoutItem(it); return it

    m = QgsLayoutItemMap(layout); m.attemptSetSceneRect(QRectF(8, 32, 292, map_h))
    m.setLayers(order); m.setExtent(ext); m.setFrameEnabled(True); m.setFrameStrokeColor(QColor("#333"))
    layout.addLayoutItem(m)

    label(eyebrow, 8, 5, 11, bold=True, color="#a07a3a", width=200)
    label(title, 8, 11, 25, bold=True, color="#6a4a24", width=260)
    label(subtitle, 9, 24, 11.5, color="#444", width=285)
    for txt, x, y, sz, col, w in annotations:
        label(txt, x, y, sz, bold=True, color=col, width=w)

    panel = QgsLayoutItemShape(layout); panel.setShapeType(QgsLayoutItemShape.Rectangle)
    panel.attemptSetSceneRect(QRectF(305, 32, 107, 256))
    panel.setSymbol(QgsFillSymbol.createSimple(
        {"color": "250,250,248,255", "outline_color": "220,220,220,255", "outline_width": "0.3"}))
    layout.addLayoutItem(panel)
    label(body, 312, 40, 10.5, color="#333", width=97)

    label(legend[0], 312, 100, 11, bold=True, color="#20140c", width=95)
    y = 110
    for sw_col, sw_txt in legend[1]:
        sq = QgsLayoutItemShape(layout); sq.setShapeType(QgsLayoutItemShape.Rectangle)
        sq.attemptSetSceneRect(QRectF(312, y, 10, 6))
        sq.setSymbol(QgsFillSymbol.createSimple(
            {"color": sw_col, "outline_color": "#c8c8c8", "outline_width": "0.2"}))
        layout.addLayoutItem(sq)
        label(sw_txt, 325, y + 0.6, 9, color="#3a2c1e", width=84); y += 6.6

    sb = QgsLayoutItemScaleBar(layout); sb.setStyle("Single Box"); sb.setLinkedMap(m)
    sb.setUnits(QgsUnitTypes.DistanceKilometers); sb.setUnitLabel("km")
    sb.setNumberOfSegments(2); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(seg_km)
    sb.setFont(QFont("Arial", 9)); sb.update(); sb.attemptMove(QgsLayoutPoint(312, 210, MM))
    layout.addLayoutItem(sb)
    na = QgsLayoutItemPicture(layout)
    na.setPicturePath(os.path.join(QgsApplication.pkgDataPath(), "svg", "arrows", "NorthArrow_02.svg"))
    na.attemptResize(QgsLayoutSize(16, 16, MM)); na.attemptMove(QgsLayoutPoint(390, 204, MM))
    layout.addLayoutItem(na)
    label(note, 8, 291, 7, color="#777", width=300)

    exp = QgsLayoutExporter(layout); st = QgsLayoutExporter.ImageExportSettings(); st.dpi = 300
    print(out_png.split("/")[-1], "export:", exp.exportToImage(out_png, st))


def supply():
    proj = _base("supply")
    hs = _hillshade(); proj.addMapLayer(hs)
    pr = _pseudocolor(PRECIP, "Annual rainfall", PRECIP_STOPS, 60, 360, opacity=0.6)
    proj.addMapLayer(pr)
    reg = _region_outline(proj)
    pts = _towns(proj)
    order = [pts] + ([reg] if reg else []) + [pr, hs]
    _layout(proj, order, REGION_EXT,
        "Supply \u2014 Where the Rain Falls",
        "Annual rainfall across Souss-Massa (NASA POWER) over the terrain that decides it",
        "Mountains decide who gets the rain. Atlantic moisture climbs the High Atlas and rains out on the "
        "windward north. By the time the air crosses to the leeward Souss and Anti-Atlas \u2014 where I am "
        "from \u2014 it is wrung dry: the far south receives about 99 mm a year, some 65% less than the "
        "northern mountains. This is the rain shadow that makes my home a desert in disguise.",
        ("Annual rainfall", [(c, f"{v} mm/yr" + ("   \u2190 desert line" if v == 250 else ""))
                             for v, c in PRECIP_STOPS]),
        "Rainfall: NASA POWER climatology, sampled on a grid and interpolated (coarse, ~50 km \u2014 the true "
        "mountain contrast is sharper). Terrain: Copernicus GLO-30 DEM. Cartography: B. Daddaoui, 2026.",
        REPO + "/figures/map_souss_supply.png",
        "A DESERT IN DISGUISE  \u00b7  SOUSS-MASSA  \u00b7  1 of 3", 50,
        annotations=[("HIGH ATLAS \u2014 windward, wet", 150, 44, 12, "#f5efe4", 120),
                     ("ANTI-ATLAS & the south \u2014\nleeward, in the rain shadow", 40, 230, 12, "#fff1e0", 110)])


def delivery():
    proj = _base("delivery")
    el = _pseudocolor(DEM, "Elevation", ELEV_STOPS, 0, 4100, opacity=1.0, fmt="{v:,.0f} m")
    proj.addMapLayer(el)
    hs = _hillshade(opacity=0.6, blend=True); proj.addMapLayer(hs)
    reg = _region_outline(proj)
    pts = _towns(proj)
    order = [pts] + ([reg] if reg else []) + [hs, el]
    _layout(proj, order, REGION_EXT,
        "Delivery \u2014 How the Water Travels",
        "The terrain of Souss-Massa: the valley between two mountain ranges that carries the water",
        "What little rain falls on the High Atlas runs downhill. The Souss valley \u2014 the corridor between "
        "the High Atlas to the north and the Anti-Atlas to the south \u2014 gathers it and carries it west to "
        "the Atlantic at Agadir. Along the way it is captured, stored, and pumped. This narrow green corridor "
        "in a dry land is where nearly everyone lives, and where the farms are.",
        ("Elevation", [(c, f"{v:,} m") for v, c in ELEV_STOPS]),
        "Terrain: Copernicus GLO-30 DEM (ESA / Copernicus), shaded relief + hypsometric tint. "
        "Region boundary: geoBoundaries. Cartography: B. Daddaoui, 2026.",
        REPO + "/figures/map_souss_delivery.png",
        "A DESERT IN DISGUISE  \u00b7  SOUSS-MASSA  \u00b7  2 of 3", 50,
        annotations=[("HIGH ATLAS", 150, 60, 12, "#f5efe4", 80),
                     ("SOUSS VALLEY \u2014 the corridor", 60, 120, 12, "#fff1e0", 110),
                     ("ANTI-ATLAS", 120, 205, 12, "#f5efe4", 80)])


def use():
    proj = _base("use")
    sat = QgsRasterLayer(
        "type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=19&zmin=0", "Satellite", "wms")
    proj.addMapLayer(sat)
    stops = [(0.10, "#c9b18a"), (0.25, "#d9d3a0"), (0.35, "#9ccb6a"),
             (0.50, "#3f9a3a"), (0.75, "#125c2a")]
    nd = _pseudocolor(NDVI, "Vegetation (NDVI)", stops, 0.10, 0.75, opacity=0.85, fmt="{v:.2f}")
    proj.addMapLayer(nd)
    pts = _towns(proj, subset={"Oulad Teima", "Taroudant"}, size="3.4")
    order = [pts, nd, sat]
    _layout(proj, order, PLAIN_EXT,
        "Use \u2014 Where the Water Goes",
        "The irrigated Souss plain (Sentinel-2 NDVI, spring 2026): citrus and greenhouses in a rain shadow",
        "Here is the disguise. In a plain that receives desert-level rainfall, roughly 162,000 hectares "
        "glow green \u2014 citrus groves and greenhouse vegetables, much of it grown for export to Europe. "
        "That green is not fed by rain. It is irrigated, largely by pumping the Souss aquifer, which is "
        "falling. Agriculture takes about 88% of Morocco's water; this is what that looks like on the ground.",
        ("Vegetation density (NDVI)", [(c, ("bare / desert" if v <= 0.10 else
                                            "sparse" if v <= 0.25 else
                                            "irrigated crops" if v <= 0.35 else
                                            "dense orchard" if v <= 0.50 else
                                            "greenhouse / citrus")) for v, c in stops]),
        "NDVI = (NIR\u2212Red)/(NIR+Red) from a 4-scene cloud-free Sentinel-2 median composite, spring 2026 "
        "(Copernicus). Basemap: Esri World Imagery. Cartography: B. Daddaoui, 2026.",
        REPO + "/figures/map_souss_use.png",
        "A DESERT IN DISGUISE  \u00b7  SOUSS-MASSA  \u00b7  3 of 3", 10,
        annotations=[("THE SOUSS PLAIN \u2014 162,000 ha irrigated\nin a rain-shadow desert", 60, 44, 12, "#ffffff", 150)],
        map_h=170)


def main(which="all"):
    if which in ("supply", "all"):
        supply()
    if which in ("delivery", "all"):
        delivery()
    if which in ("use", "all"):
        use()


def cost():
    """Panel 4 — the untold part: what a control test reveals about the green."""
    proj = _base("cost")
    sat = QgsRasterLayer(
        "type=xyz&url=https://services.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/%7Bz%7D/%7By%7D/%7Bx%7D&zmax=19&zmin=0", "Satellite", "wms")
    proj.addMapLayer(sat)
    stops = [(-0.30, "#8c510a"), (-0.15, "#d8b365"), (-0.03, "#f6e8c3"),
             (0.03, "#c7eae5"), (0.15, "#5ab4ac"), (0.30, "#01665e")]
    ch = _pseudocolor(REPO + "/data/geo/souss_change.tif",
                      "Vegetation change 2018\u21922026", stops, -0.30, 0.30,
                      opacity=0.85, fmt="{v:+.2f}")
    proj.addMapLayer(ch)
    pts = _towns(proj, subset={"Oulad Teima", "Taroudant"}, size="3.4")
    order = [pts, ch, sat]
    _layout(proj, order, PLAIN_EXT,
        "The Cost \u2014 the Disguise is Thinning",
        "Vegetation change on the Souss plain, 2018 \u2192 2026 (Sentinel-2 NDVI, matched spring windows)",
        "At first the data said the irrigated area grew 46%. That was wrong. 2026 was an exceptionally wet "
        "year, so I tested a control: bare desert that nobody irrigates. It greened by +0.09 \u2014 pure "
        "rainfall. Measured against that baseline, the land that was already farmland in 2018 is "
        "\u22120.25 NDVI LOWER in 2026. Even in a record wet year, the established farms lost green. Two "
        "explanations remain, and both mean more water stress: wells are failing, or open groves are being "
        "replaced by plastic greenhouses, which read dark to a satellite. The map raises the question; it "
        "cannot yet close it.",
        ("NDVI change 2018\u21922026", [("#01665e", "+0.30   much greener"),
                                    ("#5ab4ac", "+0.15   greener"),
                                    ("#c7eae5", "+0.03"),
                                    ("#f6e8c3", "\u22120.03   \u2248 no change"),
                                    ("#d8b365", "\u22120.15   browner"),
                                    ("#8c510a", "\u22120.30   lost its green")]),
        "NDVI from date-matched Sentinel-2 spring composites (Copernicus), reprojected to a common grid. "
        "Rainfall baseline from a bare-desert control. Basemap: Esri World Imagery. Cartography: B. Daddaoui, 2026.",
        REPO + "/figures/map_souss_cost.png",
        "A DESERT IN DISGUISE  \u00b7  SOUSS-MASSA  \u00b7  4 \u00b7 the untold panel", 10,
        annotations=[("Brown where the old farmland lost its green,\neven in a record wet year",
                      60, 44, 12, "#ffffff", 170)],
        map_h=170)


cost()

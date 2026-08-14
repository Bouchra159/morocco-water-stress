"""
build_map.py
Locator maps for the Oum Er-Rbia system — Morocco's headline water-crisis basin.

Two outputs, both from public open data (geoBoundaries + public coordinates):
  figures/fig5_basin_map.png      static map for the README
  figures/oum_er_rbia_map.html    interactive folium map

The Oum Er-Rbia feeds the Al Massira reservoir, which supplies Casablanca and
the Doukkala irrigated plain — the human stakes behind the national numbers.
"""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"
FIG = ROOT / "figures"

# regions the Oum Er-Rbia basin mainly spans
BASIN_REGIONS = ["Béni Mellal-Khénifra", "Casablanca-Settat"]

# public reference points (lon, lat), well-known coordinates
DAMS = {
    "Al Massira Dam": (-7.62, 32.53),      # main Oum Er-Rbia reservoir
    "Bin el Ouidane Dam": (-6.44, 32.10),  # El Abid tributary
}
CITIES = {
    "Casablanca": (-7.59, 33.57),  # supplied by Al Massira
    "Beni Mellal": (-6.36, 32.34),
}

CALM = "#2a6f97"
BASIN = "#e07a1f"
CRISIS = "#b3261e"
INK = "#1a1a1a"
LANDGREY = "#f0efe9"
EDGE = "#c9c9c9"


def build_static() -> None:
    adm1 = gpd.read_file(GEO / "morocco_adm1.geojson")
    adm0 = gpd.read_file(GEO / "morocco_adm0.geojson")
    basin = adm1[adm1["shapeName"].isin(BASIN_REGIONS)]

    fig, ax = plt.subplots(figsize=(9, 8.4))
    adm1.plot(ax=ax, color=LANDGREY, edgecolor=EDGE, linewidth=0.6, zorder=1)
    basin.plot(ax=ax, color=BASIN, alpha=0.35, edgecolor=BASIN,
               linewidth=1.6, zorder=2)
    adm0.boundary.plot(ax=ax, color="#7a7a7a", linewidth=0.9, zorder=3)

    # dams
    for name, (lon, lat) in DAMS.items():
        ax.scatter([lon], [lat], marker="v", s=130, color=CRISIS,
                   edgecolor="white", linewidth=1.1, zorder=5)
        ax.annotate(name, (lon, lat), textcoords="offset points",
                    xytext=(8, 4), fontsize=9, fontweight="bold", color=CRISIS)
    # cities
    for name, (lon, lat) in CITIES.items():
        ax.scatter([lon], [lat], marker="o", s=42, color=INK,
                   edgecolor="white", linewidth=0.8, zorder=5)
        ax.annotate(name, (lon, lat), textcoords="offset points",
                    xytext=(7, -11), fontsize=9, color=INK)

    # focus on the populated north-centre where the basin sits
    ax.set_xlim(-10.5, -4.0)
    ax.set_ylim(31.0, 35.2)
    ax.set_title("The Oum Er-Rbia basin and the Al Massira reservoir",
                 fontsize=14, fontweight="bold", color=INK, loc="left")
    ax.set_axis_off()

    legend = [
        mpatches.Patch(color=BASIN, alpha=0.35,
                       label="Oum Er-Rbia core regions"),
        plt.Line2D([0], [0], marker="v", color="w", markerfacecolor=CRISIS,
                   markersize=11, label="Major dam / reservoir"),
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=INK,
                   markersize=8, label="City"),
    ]
    ax.legend(handles=legend, loc="lower left", frameon=True,
              framealpha=0.9, fontsize=9)
    fig.text(0.09, 0.05,
             "Boundaries: geoBoundaries (CC BY 4.0). Dam/city points: public coordinates. "
             "Basin regions approximated to Morocco ADM1 units.",
             fontsize=8, color="#8a8a8a")
    fig.tight_layout()
    fig.savefig(FIG / "fig5_basin_map.png", bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("wrote figures/fig5_basin_map.png")


def build_interactive() -> None:
    import folium

    adm1 = gpd.read_file(GEO / "morocco_adm1.geojson")
    basin = adm1[adm1["shapeName"].isin(BASIN_REGIONS)]

    m = folium.Map(location=[32.7, -7.2], zoom_start=8, tiles="CartoDB positron")

    folium.GeoJson(
        basin.to_json(),
        name="Oum Er-Rbia core regions",
        style_function=lambda _: {
            "fillColor": BASIN, "color": BASIN,
            "weight": 2, "fillOpacity": 0.30,
        },
        tooltip=folium.GeoJsonTooltip(fields=["shapeName"], aliases=["Region:"]),
    ).add_to(m)

    for name, (lon, lat) in DAMS.items():
        folium.Marker(
            [lat, lon], tooltip=name,
            icon=folium.Icon(color="red", icon="tint", prefix="fa"),
        ).add_to(m)
    for name, (lon, lat) in CITIES.items():
        folium.CircleMarker(
            [lat, lon], radius=5, color=INK, fill=True, fill_opacity=1,
            tooltip=name,
        ).add_to(m)

    folium.LayerControl().add_to(m)
    out = FIG / "oum_er_rbia_map.html"
    m.save(str(out))
    print("wrote figures/oum_er_rbia_map.html")


def main() -> None:
    FIG.mkdir(exist_ok=True)
    build_static()
    build_interactive()


if __name__ == "__main__":
    main()

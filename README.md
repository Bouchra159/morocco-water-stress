# Running Dry: Mapping Water Stress in Morocco

> I am from the drying south of Morocco, where families are leaving because the water is
> running out. I built this to understand that — honestly, with open data — starting with
> one reservoir I could measure from space, and ending at home
> ([Where I'm from](#where-im-from)).

Morocco is one of the most water-stressed countries in the world. This is a **GIS and
remote-sensing project** — spatial analysis and cartography built from open satellite and
elevation data, fully reproducible from the scripts in `src/`.

**The GIS work in this repo:**
- 🛰️ **Satellite measurement** — the Al Massira reservoir's water surface mapped from
  Sentinel-2 every dry season, 2017–2025 (NDWI + Otsu), and vectorised to a GeoPackage
- 🗺️ **Cartography (QGIS)** — the reservoir's 2017-vs-2024 extent over satellite imagery, a
  community map of who depends on it, and shaded-relief + hypsometric terrain maps
- 🎚️ **Interactive** — a before/after satellite swipe and a scrollytelling StoryMap
- 🌿 **Spatial change analysis** — a vegetation-change (NDVI) map of the drying argan region

*The maps are the work. A few plain charts appear only as supporting context.*

![Al Massira reservoir vanishing, 2017–2025, measured from Sentinel-2](figures/reservoir_timelapse.gif)

> *The headline result: I measured the Al Massira reservoir's water surface from
> Sentinel-2 satellite imagery, every dry season from 2017 to 2025. It lost **91%**
> of its open water — the animation above is nine real measurements, not an estimate.
> Full analysis [below](#measuring-the-crisis-from-space-the-al-massira-reservoir).*

**Explore:** **[how & why I made every choice](HOW-AND-WHY.md)** ·
[the analysis](#measuring-the-crisis-from-space-the-al-massira-reservoir) ·
[who depends on it](#who-depends-on-this-water--the-community-connection) ·
[how it connects to research](REFERENCES.md) ·
[narrative notebook](notebooks/morocco_water_stress.ipynb) ·
a scrollytelling StoryMap version (`storymap/index.html`)

> **[HOW-AND-WHY.md](HOW-AND-WHY.md)** is the heart of this repo — the reasoning behind
> every decision, and an honest account of what the analysis can and cannot say. I'd
> rather you understand the *why* than be impressed by the output.

## What the data shows

- **Al Massira reservoir — which supplies Casablanca — lost 91% of its water
  surface between 2017 and 2024**, measured directly from Sentinel-2 satellite
  imagery (see [below](#measuring-the-crisis-from-space-the-al-massira-reservoir)).
- **Morocco crossed the international water-stress line (1,000 m³/person/year)
  around the year 2000.** Renewable internal freshwater fell from **2,431 m³ per
  person in 1961 to 777 m³ in 2022** — a 68% drop — and is now closer to the
  "absolute scarcity" threshold of 500 m³.
- **The water didn't shrink — the population did the opposite.** Total renewable
  internal freshwater has been essentially flat (~29 billion m³/year) while the
  population roughly tripled, from ~12 million to ~38 million. The per-capita
  collapse is driven by demand, not by a falling water supply — with drought
  making the *usable* share smaller still.
- **Agriculture uses about 88% of all water withdrawn** (2022), so any serious
  response to water stress is also a conversation about farming, subsidised
  water-intensive crops, and rural livelihoods.
- **The drought is visible in the dams.** Reported national reservoir fill rates
  fell to around **23% in 2024**, down from ~31% in 2023 — the lowest in years.

*(Plain charts of these national indicators are in [supporting context](#supporting-national-context) — but this is a spatial project, so the maps below are the real work.)*

## Measuring the crisis from space: the Al Massira reservoir

The national numbers become concrete in one place. The Oum Er-Rbia rises in the
Middle Atlas, is stored behind the **Al Massira Dam** — Morocco's second-largest
reservoir — and supplies drinking water to **Casablanca** and irrigation to the
**Doukkala plain**. So I measured it directly.

Using **Sentinel-2** satellite imagery, I computed the reservoir's open-water
surface area for every dry season from 2017 to 2025 (NDWI water index + an
automatic Otsu threshold, cloud-masked with the scene classification band). The
result is not a reported statistic — it is a measurement:

**Al Massira's water surface fell from ~98 km² (2017) to ~9 km² (2024) — a 91%
collapse — before a partial recovery to ~25 km² after the wetter 2024–25 winter.**

![Al Massira reservoir shrinking, 2017–2025](figures/fig7_reservoir_masks_grid.png)

![Al Massira water surface area time series](figures/fig6_reservoir_area_timeseries.png)

This is built in `src/measure_reservoir.py` (measurement) and
`src/build_reservoir_figures.py` (figures), from public Sentinel-2 L2A data via
the open [Earth Search](https://earth-search.aws.element84.com/v1) STAC API — no
Earth Engine account or paid service required. The method follows the published
remote-sensing literature on Al Massira and other Mediterranean reservoirs.

The water extents are vectorised (`src/export_reservoir_vectors.py`) and mapped
in **QGIS** as a high-resolution print layout (`src/qgis_reservoir_layout.py`,
project `qgis/al_massira_reservoir.qgz`), exported at 300 dpi as PNG and
print-ready PDF. The cyan line is the 2017 shoreline; the blue is what remained in
2024, and the pale ground between them is exposed lakebed:

![Al Massira 2017 shoreline vs 2024 water on satellite imagery — QGIS map](figures/map_al_massira_layout.png)

### Who depends on this water — the community connection

A shrinking reservoir is a human story, not just a hydrological one. Al Massira is
a key water source for the **Casablanca-Settat region (7.7 million people, 2024
census)** and irrigates the **Doukkala plain (~96,000 ha of farmland)** through the
Oum Er-Rbia system — and it is a **Ramsar wetland of international importance** for
birds and biodiversity. This QGIS map connects the 91% water loss to the people and
land that rely on it.

![Who depends on Al Massira — community map](figures/map_communities_al_massira.png)

Built in `src/qgis_community_map.py` from open census (HCP Morocco), irrigation
(ORMVAD), and the Sentinel-2 reservoir extents; community figures are documented
with sources in `data/raw/communities_al_massira.csv`.

### The physical story: where the water comes from

Al Massira does not make its own water — it catches it. This shaded-relief map uses
a **hypsometric tint over a hillshade** (the technique behind award-winning physical
cartography) built from the open **Copernicus 30 m DEM**, to show how Middle Atlas
snowmelt drains down the Oum Er-Rbia into the reservoir, and from there toward
Casablanca and the coast.

![The Water Journey — shaded-relief map of the Oum Er-Rbia headwaters](figures/map_water_journey.png)

Built in `src/qgis_water_journey.py` (terrain in `src/fetch_dem.py`). A lighter
terrain map (`src/qgis_basin_map.py`, over OpenTopoMap) and an interactive folium
version (`figures/oum_er_rbia_map.html`) are also included.

## Where I'm from

I did not start with Al Massira. I started at home. I am from the **Souss valley and the
Anti-Atlas** of southern Morocco (Taroudant, in Souss-Massa) — a dry land between two
mountain ranges that has grown drier in my lifetime. Where families once farmed, there is
now only enough water to drink and to wash; the one tree that endures is the **argan**.
When the water fails, people leave. The people losing their homes did least to warm the
climate — which is why, to me, this is a question of **environmental justice**.

Al Massira, in the north, is where I proved I could measure a water crisis honestly. The
reason behind it is here, in the south.

![Argan Country — the Souss valley and the Anti-Atlas](figures/map_argan_country.png)

*Home ground, from the open Copernicus DEM — `src/build_home_map.py`.*

### Measuring the drying — a spatial view

**Where the land browned.** I mapped the change in spring vegetation (Sentinel-2 NDVI)
between 2018 and 2024 across the argan slopes, over a hillshade of the terrain. The browning
(drier) concentrates in the western drainages; the signal is patchy and honest, not a
uniform collapse. This is a multi-source GIS workflow — two years of NDVI reprojected from
UTM to a common lat/lon grid, differenced into a GeoTIFF, and draped on a Copernicus-DEM
hillshade, with scale bar, north arrow, and legend (`src/build_greenness_map.py`).

![NDVI change on the argan slopes near Taroudant, 2018–2024](figures/map_greenness_change.png)

**Rainfall is the driver, over a longer record.** Annual rainfall near Taroudant has fallen
about **17 mm/decade** over 35 years, and the recent decade (2015+) averaged **~33% less
rain** than the 1990s (264 → 177 mm).

![Annual rainfall near Taroudant, 1990–2024](figures/fig_rainfall_trend.png)

*A simple year-by-year NDVI line (`figures/fig_greenness_trend.png`) is included as
supporting context — nine years is too short to prove a long-term trend on its own, which is
exactly why the 35-year rainfall record is the real signal.*

## How this connects to real research

The Al Massira decline is well documented in the peer-reviewed literature — including
Moroccan and UM6P-led work on the Oum Er-Rbia basin. My ~91% surface-loss measurement
**independently corroborates** those findings (e.g. a 2025 *Scientific Reports* study
ranking Al Massira among the most-declined Mediterranean reservoirs) and follows the same
NDWI approach as a 2023 study of the reservoir — but with a fully open, reproducible
pipeline. See **[REFERENCES.md](REFERENCES.md)** for the sources and honest framing.

## Supporting national context

Plain charts of the national indicators (World Bank data), for reference only. These are
background — the spatial analysis and maps above are the focus.

<p align="center">
  <img src="figures/fig1_percapita_decline.png" width="48%">
  <img src="figures/fig2_resource_vs_people.png" width="48%">
</p>
<p align="center">
  <img src="figures/fig3_agriculture_share.png" width="34%">
  <img src="figures/fig4_reservoir_levels.png" width="48%">
</p>

## Data sources (all public / open)

| Data | Source | Licence |
|------|--------|---------|
| Renewable freshwater per capita, totals, withdrawals, population | [World Bank Open Data](https://data.worldbank.org/country/morocco) API (indicators `ER.H2O.INTR.PC`, `ER.H2O.INTR.K3`, `ER.H2O.FWTL.ZS`, `ER.H2O.FWAG.ZS`, `SP.POP.TOTL`) | CC BY 4.0 |
| Administrative boundaries (ADM0/ADM1) | [geoBoundaries](https://www.geoboundaries.org/) | CC BY 4.0 |
| Satellite imagery (reservoir measurement) | [Sentinel-2 L2A](https://registry.opendata.aws/sentinel-2-l2a-cogs/) via [Earth Search STAC](https://earth-search.aws.element84.com/v1) | open (Copernicus) |
| Terrain / elevation (shaded relief) | [Copernicus GLO-30 DEM](https://registry.opendata.aws/copernicus-dem/) (ESA / Copernicus) | open |
| Basemap terrain | [OpenTopoMap](https://opentopomap.org/) | CC-BY-SA |
| Reservoir fill rates | Figures reported by Moroccan authorities / press (hand-entered, sourced in `data/raw/reservoir_levels_reported.csv`) | reported context |

> Note on provenance: reservoir fill rates are **not** from the World Bank API —
> they are reported figures, kept in a clearly-labelled separate file so the
> API-derived indicators stay clean. No private or basin-agency research data is
> included in this repository.

## Reproduce it

```bash
pip install -r requirements.txt

python src/fetch_worldbank.py          # pull indicators from the World Bank API
python src/fetch_geodata.py            # download open Morocco boundaries
python src/build_figures.py            # national charts -> figures/
python src/build_map.py                # static + interactive basin maps
python src/build_reservoir_figures.py  # Sentinel-2 Al Massira analysis (downloads imagery)
python src/export_reservoir_vectors.py # vectorise water masks -> GeoPackage
python src/fetch_truecolor.py          # true-colour 2017/2024 crops for the swipe
python src/build_home_map.py           # "Argan Country" home-region terrain map
python src/measure_rainfall.py         # 35-yr rainfall trend near home (NASA POWER)
python src/measure_greenness.py        # spring NDVI trend on the argan slopes (Sentinel-2)
python src/build_greenness_map.py      # NDVI-change GIS map over a DEM hillshade
python src/fetch_dem.py                # Copernicus 30m DEM for shaded relief
python src/build_method_figures.py     # teaching figures: NDWI/Otsu histogram, area vs volume
python src/build_reservoir_gif.py      # animated timelapse GIF
python src/build_storymap.py           # self-contained scrollytelling page

# these run inside QGIS (Plugins -> Python Console), not the plain venv:
#   src/qgis_basin_map.py          terrain map of the basin
#   src/qgis_reservoir_layout.py   high-res 2017-vs-2024 satellite map
#   src/qgis_community_map.py       "who depends on Al Massira" map
#   src/qgis_water_journey.py       shaded-relief + hypsometric terrain map
```

## Repository layout

```
morocco-water-stress/
├── src/                 data fetch, analysis, figure/map/GIF/story builders
├── data/
│   ├── raw/             World Bank JSON, reported reservoir + community CSVs
│   ├── processed/       tidy indicator CSVs, reservoir areas + masks
│   └── geo/             open boundaries + measured water GeoPackage
├── figures/             all charts, maps, the timelapse GIF, PDFs
├── qgis/                QGIS projects (terrain, reservoir, community maps)
├── notebooks/           narrative walkthrough
├── storymap/            self-contained scrollytelling StoryMap page
└── REFERENCES.md        how this connects to peer-reviewed research
```

## Why this project

Water is Morocco's defining environmental challenge, and it is also a community
one: who gets water, for which crops, in which basin. This repo is a small,
honest attempt to make that visible with open data and reproducible code.

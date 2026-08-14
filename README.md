# Running Dry: Mapping Water Stress in Morocco

Morocco is one of the most water-stressed countries in the world. This project
uses open data to tell that story at two scales — the national trend since 1961,
and a zoom into the **Oum Er-Rbia basin**, whose Al Massira reservoir supplies
Casablanca and the Doukkala irrigated plain.

Everything here is built from **public, openly licensed data** and is fully
reproducible from the scripts in `src/`.

![Per-capita renewable freshwater decline](figures/fig1_percapita_decline.png)

## What the data shows

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

<p align="center">
  <img src="figures/fig2_resource_vs_people.png" width="49%">
  <img src="figures/fig3_agriculture_share.png" width="49%">
</p>

## Zooming in: the Oum Er-Rbia basin

The national numbers become concrete in one basin. The Oum Er-Rbia rises in the
Middle Atlas, is stored behind the **Al Massira Dam**, and from there supplies
drinking water to Casablanca and irrigation to the Doukkala plain. When the
Atlas snowpack and rains fail, this is where the shortfall is felt.

![Oum Er-Rbia basin — QGIS terrain map](figures/qgis_basin_map.png)

The terrain map above is scripted with **PyQGIS** (`src/qgis_basin_map.py`) over
OpenTopoMap; a lighter Python version (`src/build_map.py`) produces both a static
map and an interactive `figures/oum_er_rbia_map.html`.

## Data sources (all public / open)

| Data | Source | Licence |
|------|--------|---------|
| Renewable freshwater per capita, totals, withdrawals, population | [World Bank Open Data](https://data.worldbank.org/country/morocco) API (indicators `ER.H2O.INTR.PC`, `ER.H2O.INTR.K3`, `ER.H2O.FWTL.ZS`, `ER.H2O.FWAG.ZS`, `SP.POP.TOTL`) | CC BY 4.0 |
| Administrative boundaries (ADM0/ADM1) | [geoBoundaries](https://www.geoboundaries.org/) | CC BY 4.0 |
| Basemap terrain | [OpenTopoMap](https://opentopomap.org/) | CC-BY-SA |
| Reservoir fill rates | Figures reported by Moroccan authorities / press (hand-entered, sourced in `data/raw/reservoir_levels_reported.csv`) | reported context |

> Note on provenance: reservoir fill rates are **not** from the World Bank API —
> they are reported figures, kept in a clearly-labelled separate file so the
> API-derived indicators stay clean. No private or basin-agency research data is
> included in this repository.

## Reproduce it

```bash
pip install -r requirements.txt

python src/fetch_worldbank.py   # pull indicators from the World Bank API
python src/fetch_geodata.py     # download open Morocco boundaries
python src/build_figures.py     # charts -> figures/
python src/build_map.py         # static + interactive basin maps
# src/qgis_basin_map.py runs inside QGIS (Python console) for the terrain map
```

## Repository layout

```
morocco-water-stress/
├── src/                 data fetch + figure/map builders
├── data/
│   ├── raw/             raw World Bank JSON + reported reservoir CSV
│   ├── processed/       tidy indicator CSVs
│   └── geo/             open Morocco boundaries (geoBoundaries)
├── figures/            all charts + maps (PNG, interactive HTML)
├── qgis/               QGIS project for the terrain map
└── notebooks/          narrative walkthrough
```

## Why this project

Water is Morocco's defining environmental challenge, and it is also a community
one: who gets water, for which crops, in which basin. This repo is a small,
honest attempt to make that visible with open data and reproducible code.

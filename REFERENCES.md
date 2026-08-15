# How this project connects to real research

This repository is a small, open, reproducible project — but it is not working in a
vacuum. The Oum Er-Rbia basin and the Al Massira reservoir are an active subject of
peer-reviewed research, much of it led by Moroccan institutions. This page places my
work honestly alongside that literature.

## What my contribution is (and isn't)

- **I did not discover that Al Massira is shrinking** — that is well documented. My aim
  was to *measure it independently, from open data, with fully reproducible code* that
  anyone can rerun.
- **My result corroborates published findings.** I measure the reservoir's open-water
  surface falling ~91% between 2017 and 2024. Independent studies report Al Massira as
  among the most severely declined reservoirs in the Mediterranean region over a similar
  period, and describe its storage dropping to only a few percent of capacity.
- **What I add** is an end-to-end open pipeline (World Bank API → Sentinel-2 NDWI+Otsu →
  QGIS cartography) and a community-facing framing of *who* depends on the water, rather
  than a new scientific method.

## Regional research (Oum Er-Rbia, Al Massira, Moroccan water)

Verified, peer-reviewed sources I read while building this:

- **Monitoring water crisis from space across a Mediterranean region** — *Scientific
  Reports* (Nature), 2025.
  [nature.com/articles/s41598-025-06240-1](https://www.nature.com/articles/s41598-025-06240-1)
  — reports Al Massira among the most pronounced reservoir declines; directly relevant to my measurement.
- **Use of Spatial Remote Sensing to Study the Temporal Evolution of the Water Retention
  of Al Massira Dam in Morocco** — 2023.
  [ResearchGate](https://www.researchgate.net/publication/367763659) — closest prior work:
  NDWI-based monitoring of Al Massira's water surface. My project follows and extends this
  approach with an open, reproducible pipeline.
- **Analysis of the Propagation Characteristics of Meteorological Drought to Hydrological
  Drought … in the Oum Er Rbia Watershed, Morocco** — *Remote Sensing* (MDPI), 2025.
  [doi.org/10.3390/rs17020281](https://doi.org/10.3390/rs17020281)
- **Temporal relationships between agricultural and meteorological drought over the Oum Er
  Rbia River, Morocco** — *Big Earth Data*, 2025 (International Water Research Institute,
  UM6P, with UQTR).
  [tandfonline.com](https://www.tandfonline.com/doi/full/10.1080/20964471.2025.2479430)
- **Spatiotemporal characterization and hydrological impact of drought patterns in
  northwestern Morocco** — *Frontiers in Water*, 2024.
  [frontiersin.org](https://www.frontiersin.org/journals/water/articles/10.3389/frwa.2024.1463748/full)
- **Evaluation of GRACE / GRACE-FO derived products for water storage assessment in
  Moroccan aquifers** — *Geocarto International*, 2025.
  [tandfonline.com](https://www.tandfonline.com/doi/full/10.1080/10106049.2025.2521829)
- **Assessment of drought variability in the Marrakech-Safi region (Morocco) using GIS and
  remote sensing** — *Water Supply* (IWA), 2023.
  [iwaponline.com](https://iwaponline.com/ws/article/23/11/4592/98297)

Leading Moroccan hubs for this research include UM6P's **Center for Remote Sensing
Applications (CRSA)** and its **International Water Research Institute (IWRI)** — the kind
of community this project is meant to connect with.

## Context worth knowing

Several of these studies link the reservoir decline not only to prolonged drought (since
~2017) but also to expanded irrigation of water-intensive crops under national agricultural
policy — a reminder that water scarcity here is as much about *choices* as about rainfall.

> Note: this is a personal open-data project, not a peer-reviewed study. Citations are
> provided so readers can go to the primary sources; any errors of framing are my own.

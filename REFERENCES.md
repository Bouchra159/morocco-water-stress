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

## The Souss-Massa groundwater literature, and what it says about my fourth map

My fourth Souss map found that land which was farmland in 2018 had lost vegetation by 2026,
even after I subtracted the wet-year rainfall baseline. I could not tell you why. My own test
for separating failing farms from plastic greenhouses was not reliable enough to trust, so the
repo reports it as inconclusive.

Published work on this exact basin can say more than my data can. I am putting it here because
the honest position is that my measurement raised the question and other people's research
answers it.

**El Garouani and colleagues (2026), "The Spectral Illusion of Crop Health: Evaluating the
Groundwater Cost of Agricultural Maladaptation in the Souss-Massa Basin (Morocco)",
*Hydrology*, 13(5), 132. [doi:10.3390/hydrology13050132](https://doi.org/10.3390/hydrology13050132)**

Studying 1995 to 2021 in my region, they describe what they call a scissors effect: rainfall
and natural recharge falling while pumping rises. Cereal areas shrank and irrigated fodder
crops expanded, especially alfalfa and fodder maize, which need up to 800 mm of water per
cycle in a place that receives about 99 mm of rain a year. Their central point is the one that
matters most for my work: the resulting groundwater crisis is *"paradoxically masked from space
by an artificial attenuation of water stress"*. Fields can look healthy from orbit while the
aquifer beneath them empties. They call this the spectral illusion.

That is a caution aimed directly at the method I used. A vegetation index measures the canopy,
not the water table. Green is not proof that the water is there; it can be proof that someone
is pumping harder.

**Ouatiki and colleagues (2025), "Evaluation of GRACE and GRACE-FO derived products for water
storage assessment in Moroccan aquifers", *Geocarto International*.
[doi:10.1080/10106049.2025.2521829](https://doi.org/10.1080/10106049.2025.2521829)**

Shows that the GRACE gravity satellites can track water storage in Moroccan aquifers, and
reports a clear downward trend. This is the measurement my project is missing: I mapped the
surface, and GRACE weighs what is underneath. Groundwater in the Souss-Massa basin has fallen
by roughly 20 to 65 metres over the last thirty years.

**What this means for my conclusions**

It does not change any number I measured, and I have not edited my maps to agree with it. What
it changes is the reading of my fourth map. Of the two explanations I could not separate,
failing wells or plastic greenhouses, the literature says groundwater depletion in this basin
is real, severe and well documented. My data is consistent with that. It still does not prove
it, and I would need GRACE or well records to say so myself.

## Context worth knowing

Several of these studies link the reservoir decline not only to prolonged drought (since
~2017) but also to expanded irrigation of water-intensive crops under national agricultural
policy — a reminder that water scarcity here is as much about *choices* as about rainfall.

> Note: this is a personal open-data project, not a peer-reviewed study. Citations are
> provided so readers can go to the primary sources; any errors of framing are my own.

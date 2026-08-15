# StoryMap build guide — "Running Dry: Morocco's Water Crisis"

Everything you need to assemble the Esri StoryMap at
[storymaps.arcgis.com](https://storymaps.arcgis.com) (free personal account —
sign up with a personal email so you keep access after graduation).

Each section below gives you: the **copy to paste**, the **figure to upload**
(from this repo's `figures/` folder), and the **data callout** to feature.
All numbers are the real values computed in this repo — safe to cite.

> Build order tip: create the cover first, then add one "sidecar" or "immersive"
> block per section. Total assembly time ~1–1.5 hours since the writing + data
> are already done here.

---

## Cover panel

- **Format:** full-bleed cover, title + subtitle.
- **Title:** `Running Dry`
- **Subtitle:** `Mapping Morocco's water crisis, community by community`
- **Byline:** your name + "Data & maps from open sources · 2026"
- **Background image:** a dry-reservoir / Moroccan farmland photo. Get one that
  is licensed for reuse — search [Unsplash](https://unsplash.com/s/photos/morocco-drought)
  or [Wikimedia Commons](https://commons.wikimedia.org/) and **credit the photographer**.
  (Don't use a random Google image — reviewers notice, and licensing matters.)

---

## Section 1 — The national picture

**Copy:**
> Morocco has crossed a line that hydrologists use to define water stress. In
> 1961 each Moroccan had about **2,431 cubic metres** of renewable freshwater a
> year. By 2022 that had fallen to **777 cubic metres** — a 68% drop, and below
> the international water-stress threshold of 1,000 m³. The country is now moving
> toward the 500 m³ mark that defines "absolute scarcity."

- **Figure:** `figures/fig1_percapita_decline.png`
- **Data callout (big number block):** `777 m³` — "renewable freshwater per
  person, 2022 (down from 2,431 in 1961)."
- **Source line:** World Bank Open Data, indicator ER.H2O.INTR.PC.

---

## Section 2 — Why: same water, three times the people

**Copy:**
> Here is the part that surprises people: Morocco's water supply has not
> collapsed. The total renewable freshwater has stayed almost flat — around
> **29 billion cubic metres a year** — for six decades. What changed is the
> number of people sharing it. The population roughly tripled, from about
> 12 million to 38 million. The crisis is one of demand meeting a hard limit —
> and drought makes the usable share smaller still.

- **Figure:** `figures/fig2_resource_vs_people.png`
- **Data callout:** `×3` — "population growth since 1961, against a fixed water supply."

---

## Section 3 — Where the water goes

**Copy:**
> Any honest conversation about Morocco's water is a conversation about farming.
> Agriculture accounts for roughly **88% of all the freshwater withdrawn** in the
> country. Decades of policy encouraged water-intensive crops — citrus, melons,
> avocados — often for export. That makes water stress inseparable from rural
> livelihoods, food, and the choices made about which crops a dry country grows.

- **Figure:** `figures/fig3_agriculture_share.png`
- **Data callout:** `88%` — "of Morocco's water withdrawals go to agriculture."

---

## Section 4 — The drought you can see: the dams

**Copy:**
> The abstract numbers become visible in the reservoirs. National dam fill rates
> fell to around **23% in 2024**, down from about 31% the year before — among the
> lowest levels in years, after a run of dry winters. When the dams are this low,
> cities and farms are drawing down a shrinking buffer.

- **Figure:** `figures/fig4_reservoir_levels.png`
- **Data callout:** `23%` — "national reservoir fill rate, 2024."
- **Honesty note to keep in the caption:** "Reservoir figures are reported by
  Moroccan authorities and press, not the World Bank." (Being transparent about
  this *strengthens* the piece.)

---

## Section 5 — A reservoir vanishing: Al Massira from space  ⭐ centrepiece

This is the strongest section — an **original measurement**, not a cited
statistic. It's the "geographic zoom-in" the externship teaches, done with real
satellite analysis.

**Copy:**
> To see what water stress means on the ground, follow one river. The Oum Er-Rbia
> rises in the Middle Atlas, gathers snowmelt and rain, and is stored behind the
> **Al Massira Dam** — Morocco's second-largest reservoir, which supplies
> **Casablanca** and the **Doukkala** irrigated plain. I measured the reservoir
> directly from Sentinel-2 satellite imagery: its open-water surface fell from
> about **98 km² in 2017 to just 9 km² in 2024 — a 91% collapse** — before a
> partial recovery after the wetter 2024–25 winter. The blue you lose between
> those two years is exposed lakebed.

- **Hero image (full-bleed):** `figures/map_al_massira_layout.png` — the
  high-resolution QGIS map (cyan 2017 shoreline vs 2024 water on satellite
  imagery). This is your single most impressive visual — lead with it.
- **Supporting:** `figures/fig7_reservoir_masks_grid.png` (the year-by-year
  shrink) and `figures/fig6_reservoir_area_timeseries.png` (the −91% curve).
- **Context map:** `figures/qgis_basin_map.png` (terrain map of the basin).
- **Data callout:** `−91%` — "of Al Massira's water surface, 2017–2024 (measured
  from Sentinel-2)."

---

## Section 6 — Human impact & community

This is the section that turns a data project into a **community conservation**
story. Write 2–3 short paragraphs **in your own voice** — this is where local
knowledge beats any dataset. Prompts to answer:
- What does a dry year mean for a farming family in the basin?
- Who bears the cost first — smallholders, or large irrigated estates?
- What everyday changes (water cuts, rationing, well-drilling) do households see?

No figure needed — a single evocative photo (properly credited) works best here.

---

## Section 7 — What's being done

**Copy (adapt as you like):**
> Morocco is not standing still. The response spans big infrastructure and small
> fields: new **desalination** plants (including one of Africa's largest, planned
> for Casablanca), a national push toward **drip irrigation** to cut agricultural
> waste, **aquifer-recharge** and water-transfer schemes, and tighter limits on
> the most water-hungry crops. The open question is whether supply-side fixes can
> keep pace with demand — or whether the harder conversation is about *what*
> a water-scarce country chooses to grow.

- No figure required, or reuse the basin map.

---

## Closing panel

**Copy:**
> Water is Morocco's defining environmental challenge — and a deeply local one.
> Who gets water, for which crops, in which basin, is a question of geography and
> of community. Making it visible with open data is a first step toward
> answering it well.

- Add a "Credits" block listing the data sources (copy the table from the repo
  README) and a link to the GitHub repo once it's public.

---

## Asset checklist

| Section | Asset in this repo |
|---------|--------------------|
| 1 | `figures/fig1_percapita_decline.png` |
| 2 | `figures/fig2_resource_vs_people.png` |
| 3 | `figures/fig3_agriculture_share.png` |
| 4 | `figures/fig4_reservoir_levels.png` |
| 5 | `figures/map_al_massira_layout.png` (hero) + `fig7_reservoir_masks_grid.png` + `fig6_reservoir_area_timeseries.png` + `qgis_basin_map.png` |
| 6–7 | credited photos from Unsplash / Wikimedia Commons |

**Two things only you can supply:** (1) properly-licensed photos, and (2) the
Section 6 community voice. Everything else is ready in `figures/`.

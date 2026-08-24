# Esri StoryMaps build kit — *Morocco's Vanishing Water*

Everything to assemble the capstone StoryMap at **[storymaps.arcgis.com](https://storymaps.arcgis.com)**
(sign in with your ArcGIS account — use a **personal** email so you keep access after graduation).

This kit mirrors the finished web StoryMap exactly. Every number is a real value computed in this
repo, so it is safe to cite. Assembly time ≈ 45 min because the writing, data, and maps are done.

**How to use this file**
- Each block below gives you: the **block type** to add in ArcGIS StoryMaps, the **copy to paste**,
  the **image to upload** (already staged and numbered in `storymap/esri_assets/`), and the
  **alt text**.
- The images in `esri_assets/` are numbered in the exact order they appear — just upload them top to bottom.
- Block types map to StoryMaps' "+" menu: **Cover**, **Text**, **Image**, **Separator**,
  **Sidecar** (image + scrolling text), **Immersive → Slideshow**, and the **Quote** style for pull lines.

---

## 0 · Cover  *(block: Cover — "full" option)*

- **Title:** `Morocco's Vanishing Water`
- **Subtitle:** `A reservoir, a home, and the drying south — measured from open satellites`
- **Byline:** `Bouchra Daddaoui · maps & analysis from open data · 2026`
- **Cover image:** `esri_assets/00_cover.png` *(the argan-country terrain — it reads as "home" and sets the tone)*.
  If you prefer a photo, source one licensed for reuse from
  [Wikimedia Commons](https://commons.wikimedia.org/) and **credit the photographer**; never a random Google image.

---

## 1 · The national picture  *(block: Text + Image)*

**Paste:**
> Morocco has crossed a line hydrologists use to define water stress. In 1961 each Moroccan had about
> **2,431 cubic metres** of renewable freshwater a year. By 2022 that had fallen to **777 cubic metres** —
> a 68 % drop, and below the international water-stress threshold of 1,000 m³.

- **Image:** `esri_assets/01_percapita.png`
- **Alt:** *Renewable freshwater per person in Morocco, 1961–2022, falling below the water-stress line.*
- **Source line (small text under image):** World Bank Open Data (ER.H2O.INTR.PC).
- **Optional big-number block (Text, large):** **777 m³** — freshwater per person, 2022 (down from 2,431 in 1961).

---

## 2 · Why — same water, three times the people  *(block: Text + Image, then Image)*

**Paste:**
> The surprise is that Morocco's supply has not collapsed. Total renewable freshwater has stayed almost
> flat — around **29 billion m³** — while the population **tripled**, from about 12 million in 1961 to
> 38 million today. The crisis is demand meeting a fixed supply. And most of that demand is farming:
> **agriculture takes about 88 %** of all the water Morocco withdraws.

- **Image A:** `esri_assets/02_supply_vs_people.png` — *Flat water supply against a tripling population.*
- **Image B:** `esri_assets/03_agriculture_share.png` — *Agriculture uses 88 % of Morocco's freshwater withdrawals.*
- **Source:** World Bank Open Data.

---

## 3 · The water journey  *(block: Sidecar)*

**Paste (narrative panel):**
> Morocco's water starts high. Winter snow and rain on the Middle Atlas — peaks above **3,000 m** —
> drain down the Oum Er-Rbia river and collect behind one dam: **Al Massira**. From this single reservoir,
> water travels northwest to Casablanca and the Doukkala farmland. When the mountains get less snow,
> everything downstream feels it.

- **Image:** `esri_assets/04_water_journey.png`
- **Alt:** *Shaded-relief map of the Middle Atlas draining into the Al Massira reservoir. Made in QGIS.*
- **Caption:** Copernicus GLO-30 DEM, hillshade + hypsometric tint. **Made in QGIS.**

---

## 4 · Al Massira — collapse, and comeback  *(block: Immersive → Slideshow)*

This is the evidence core. Use a 4-slide slideshow.

**Intro text above the slideshow:**
> I measured the reservoir itself from space — no proprietary tools, just open Sentinel-2 imagery and a
> water-detection index (NDWI + Otsu thresholding). The story is not a straight line down. It is
> **whiplash**: **98 km² in 2017 → 9 km² in 2024** (a 91 % collapse in the drought) → **125 km² by 2026**,
> after Morocco's record 2025–26 rains refilled the dams. The volatility *is* the climate story.

- **Slide 1 — Timelapse:** `esri_assets/05_timelapse.gif` · *Al Massira draining and refilling, 2017–2026.*
- **Slide 2 — Yearly masks:** `esri_assets/06_masks_grid.png` · *Year-by-year satellite water masks, 2017–2026.*
- **Slide 3 — Area curve:** `esri_assets/07_area_timeseries.png` · *Water-surface area, 2017–2026 (the V-shape).*
- **Slide 4 — QGIS map:** `esri_assets/08_reservoir_map.png` · *2017 shoreline vs 2024 drought water, QGIS.*

**Optional swipe:** StoryMaps has a **Swipe** block — load `esri_assets/09a_truecolor_2017.jpg` (left) and
`esri_assets/09b_truecolor_2024.jpg` (right) for a true-colour before/after of the reservoir.

**Big-number block:** **−91 %** water surface, 2017 → 2024 · then **+1,300 %** rebound by 2026.

---

## 5 · A reservoir is a community  *(block: Text + Image)*  — section tint on

**Paste:**
> A shrinking blue shape is easy to scroll past, so here is what it holds. The water behind Al Massira
> reaches the **Casablanca-Settat region — 7.7 million people** (2024 census) — and irrigates roughly
> **96,000 hectares** of Doukkala farmland. Al Massira is also a **Ramsar site**, a wetland of international
> importance for birds. When the reservoir falls, it is their taps, their harvests, and that wetland that feel it first.

- **Image:** `esri_assets/10_communities.png`
- **Alt:** *Map of the communities and farmland that depend on the Al Massira reservoir. Made in QGIS.*
- **Quote block (pull line):** *"This is the water my own country runs on."*

---

## 6 · Following the water to the fields  *(block: Text + Image)*

**Paste:**
> A reservoir only matters because of what it waters. So I followed the water downstream to the **Doukkala
> plain** and measured crop moisture (Sentinel-2 **NDMI**) on the fields themselves. Through the drought the
> crops were moisture-stressed — and when the 2025–26 rains refilled the dam, the fields came back with it.
> The green below is the farmland recovering between 2024 and 2026.

- **Image:** `esri_assets/11_crop_stress.png`
- **Alt:** *Crop water-stress recovery on the Doukkala plain, 2024→2026, from Sentinel-2 NDMI. Made in QGIS.*
- **Quote block:** *"Reservoir → farmland → food. The whole chain moves together — which is how you know the measurement is real."*

---

## 7 · Where I'm from — and where everyone goes  *(block: Sidecar, multi-image)*

**Paste (narrative panel):**
> I did not start caring about water in the north. I started at home, in the **south** — the Souss valley and
> the Anti-Atlas, where I am from. It is a dry land between two mountain ranges, and in my lifetime it has grown
> drier. Where families once farmed, there is now only enough water to drink and to wash. The one tree that
> still holds on is the **argan**, because it can live on almost nothing.
>
> When the water fails, people do the one thing the land will no longer let them do: they leave. That is the
> quiet question under all of this — not only how much water is left, but **where everyone goes** when a place
> can no longer hold them. The people losing their homes did the least to warm the climate. To me, that is what
> **environmental justice** means: the difference between a family staying and a family leaving.

- **Image A:** `esri_assets/12_argan_terrain.png` — *Home: the Souss valley between the High Atlas and the Anti-Atlas. QGIS shaded relief.*
- **Image B:** `esri_assets/13_greenness.png` — *Vegetation change on the argan slopes (Sentinel-2 NDVI, 2018–2026). QGIS.*
- **Image C:** `esri_assets/14_landcover.png` — *Land cover near Taroudant, unsupervised K-means classification. QGIS.*
- **Image D:** `esri_assets/15_modis_trend.png` — *25 years of vegetation (MODIS NDVI, 2000–2026): a modest decline with big rainfall-driven swings.*

---

## 8 · Does it all hang together?  *(block: Text)*

**Paste:**
> Four independent measurements — a reservoir, rainfall, crop moisture, and 25 years of vegetation — all crash
> in the drought and all recover in 2026. When independent datasets agree, that is how you know the story is
> real and not cherry-picked. The honest reading is not "Morocco is simply drying up." It is **violent
> volatility**: a drying long-term baseline, a brutal multi-year drought, and a sharp wet-year recovery.

Optional table block:

| Signal | Drought (2017→2024) | Recovery (2025–26) |
|---|---|---|
| Reservoir surface | 98 → 9 km² (−91 %) | → 125 km² |
| Rainfall (Taroudant) | ~31 % below 1990s | anomalously wet |
| Doukkala crop moisture | stressed (neg. NDMI) | +0.24 |
| Argan vegetation (25 yr) | dips through 2015–24 | rebounds 2026 |

---

## 9 · What can be done  *(block: Text)*

**Paste:**
> None of this is hopeless. The same open data that measures the crisis can guide the response: drip
> irrigation and less thirsty crops on the 88 % that goes to farming; treated-wastewater reuse and desalination
> powered by Morocco's abundant sun; protecting recharge zones and wetlands like Al Massira; and — most of all —
> planning for the people already on the move, so leaving is a choice and not the only option left.

---

## 10 · Credits & author note  *(block: Text)*

**Paste:**
> Made by **Bouchra Daddaoui**, 2026. Every map and number here comes from **open, public data** —
> Sentinel-2 (Copernicus), the Copernicus GLO-30 DEM, NASA POWER, MODIS, and the World Bank — and is fully
> reproducible from the code at *github.com/Bouchra159/morocco-water-stress*. I built this because the drying
> south is not a statistic to me. It is home.

- **Data & method:** Sentinel-2 via Earth Search (NDWI + Otsu; NDMI; NDVI), Copernicus DEM, NASA POWER,
  ORNL MODIS, World Bank Open Data. Maps in **QGIS** and **ArcGIS Pro**.

---

### Build tips
- Keep one **accent colour** (a deep water-teal) and one **serif heading font** for a documentary feel.
- Put the four big numbers (777 m³ · 88 % · −91 % · 7.7 M) in **large number blocks** — they anchor the scroll.
- Every map caption should say **"Made in QGIS"** or **"ArcGIS Pro"** — reviewers for a GIS role look for that.
- Publish as **unlisted** first, review on your phone, then set to **public** and share the link in your application.

---

## 7b · A Desert in Disguise — Souss-Massa in four maps  *(block: Sidecar, or Text + 4 Images)*

Place this **after section 7 (Where I'm from)**. It applies National Geographic's own
*California: A Desert in Disguise* structure — Supply → Delivery → Use, plus the fourth
"untold" map that lesson asks you to design — to Bouchra's home region.

**Intro text:**
> National Geographic teaches California's water story in three maps — **where the water comes
> from, how it travels, and who uses it** — then challenges you to design a fourth for the part
> the first three leave out. I built that structure for **Souss-Massa**, my own region, with my
> own measurements.

**1 · Supply** — image `esri_assets/16_souss_supply.png`
> Atlantic moisture climbs the High Atlas and rains out on the windward north. By the time the
> air crosses to the leeward side it has been wrung dry. That is the **rain shadow**, and my home
> sits inside it: **99 mm of rain a year in the far south against 287 mm in the northern
> mountains — 65% less**. The desert here is not an accident of latitude. It is made by the mountains.
- *Caption:* Annual rainfall across Souss-Massa (NASA POWER) over Copernicus DEM terrain. Made in QGIS.

**2 · Delivery** — image `esri_assets/17_souss_delivery.png`
> Between the High Atlas and the Anti-Atlas runs one valley that gathers what little falls and
> carries it west to the Atlantic. Almost everyone lives along it. Almost every farm is in it.
- *Caption:* The Souss corridor, shaded relief from the Copernicus GLO-30 DEM. Made in QGIS.

**3 · Use** — image `esri_assets/18_souss_use.png`
> Here is the disguise: in a plain with desert-level rainfall, roughly **162,000 hectares glow
> green** — citrus and greenhouse vegetables, much of it for export. That green does not come
> from the sky. It is pumped out of the ground.
- *Caption:* Irrigated land on the Souss plain (Sentinel-2 NDVI, spring 2026). Made in QGIS.

**4 · The Cost** — image `esri_assets/19_souss_cost.png`
> For the fourth map I asked the obvious question: is that green growing or shrinking? The data
> said it **grew 46%**. I nearly published that. It was wrong. 2026 was an exceptionally wet year,
> so I ran a **control** — bare desert that nobody irrigates. It greened **+0.09** on its own,
> purely from rain. Measured against that baseline the truth reverses: land that was **already
> farmland in 2018 is −0.25 lower in 2026**. The established farms lost green *even in a record
> wet year*.
- *Caption:* Vegetation change 2018→2026, date-matched spring composites. The brown rectangles are real fields. Made in QGIS.

**Quote block:**
> *"A control test is the difference between a map that informs and a map that misleads. Mine
> nearly misled me."*

**Optional table block** (the control test):

| | Mean NDVI change 2018→2026 | vs rainfall baseline |
|---|---|---|
| Bare desert (control) | +0.094 | — (this *is* the baseline) |
| Sparse rangeland | +0.061 | −0.034 |
| Farmland in 2018 | −0.160 | **−0.255** |

# Running Dry: mapping water stress in Morocco

I am from the south of Morocco, where the water is running out and people are leaving.

I grew up hearing that things used to be different, that there used to be farming here. I
wanted to know whether that was true or whether it was just the kind of thing people say about
the past. So I learned to measure it.

This is what I found, built entirely from free satellite data. Every number comes from a script
in `src/`, so anyone can run it and check me.

![Al Massira reservoir, 2017 to 2026, measured from Sentinel-2](figures/reservoir_timelapse.gif)

## Morocco has less water than it used to, but not for the reason I expected

In 1961 there were about 2,431 cubic metres of renewable freshwater per person here. By 2022
there were 777. That is a 68% drop, and it puts Morocco below the line hydrologists use to
define water stress.

But the water did not disappear. The total has stayed roughly flat, around 29 billion cubic
metres a year. What changed is that the population tripled, from 12 million to 38 million. And
88% of the water that gets used goes to farming.

So this is not really a story about rain. It is a story about how many of us there are, and
what we choose to grow.

## I measured one reservoir from space

The Al Massira dam holds the water Casablanca drinks. I wanted to watch it change, so I
measured its surface from Sentinel-2 images every dry season from 2017 to 2026, using a water
index and an automatic threshold, with clouds masked out.

It fell from 98 square kilometres to 9. That is a 91% collapse.

Then in 2026 it came back to 125, bigger than when I started, after the record rains of 2025
and 2026 refilled Morocco's dams.

![Al Massira water surface each year, 2017 to 2026](figures/fig7_reservoir_masks_grid.png)

![The reservoir's surface area over time](figures/fig6_reservoir_area_timeseries.png)

I had already written "the vanishing reservoir" before I extended the data to 2026. I was
wrong. The real story is not that the water is disappearing, it is that it swings violently
between drought and flood. That is harder to live with than a slow decline, because you cannot
plan around it.

The cyan line below is the 2017 shoreline. The blue is what was left in 2024. Everything
between them was lakebed.

![The 2017 shoreline against the 2024 water](figures/map_al_massira_layout.png)

## Who that water belongs to

A blue shape getting smaller is easy to scroll past, so here is what it holds. The water behind
Al Massira reaches 7.7 million people in the Casablanca-Settat region, and irrigates about
96,000 hectares of farmland on the Doukkala plain. It is also a Ramsar wetland, protected for
its birds.

![The communities that depend on Al Massira](figures/map_communities_al_massira.png)

A reservoir only matters because of what it waters, so I followed it downstream and measured
crop moisture in the Doukkala fields. They dried out through the drought and came back in 2026,
tracking the dam. Reservoir, farmland, food. The chain holds.

![Crop moisture recovering on the Doukkala plain](figures/map_qgis_crop_stress.png)

The water starts higher still, as snow and rain on the Middle Atlas, running down the Oum
Er-Rbia into the dam.

![Where the water begins](figures/map_water_journey.png)

## Home

I did not start caring about water in the north. I started at home, in Souss-Massa.

It is a dry place between two mountain ranges, and in my lifetime it has grown drier. Where
families used to farm there is now only enough water to drink and to wash. The tree that holds
on is the argan, because it can live on almost nothing. When the water fails, people do the one
thing the land will not let them do any more. They leave.

The people losing their homes did the least to cause the warming. That is what environmental
justice means to me. Not an abstraction, but the difference between a family staying and a
family going.

![Argan country, the Souss valley and the Anti-Atlas](figures/map_qgis_argan_terrain.png)

I told this region in four maps, following the structure National Geographic uses to teach
California's water: where it comes from, how it travels, who uses it, and then one more map for
what the first three leave out.

### 1. Supply

Mountains decide who gets water. Atlantic air climbs the High Atlas and drops its rain on the
windward north. By the time it crosses to my side it has nothing left. The far south gets 99 mm
of rain a year. The northern mountains get 287.

The desert here is not an accident of latitude. The mountains make it.

![The rain shadow of the High Atlas](figures/map_souss_supply.png)

### 2. Delivery

One valley runs between the High Atlas and the Anti-Atlas, gathering what little falls and
carrying it west to the sea. Almost everyone lives along it. Almost every farm is in it.

![The Souss corridor](figures/map_souss_delivery.png)

### 3. Use

Here is the strange part. In a plain with desert rainfall, about 162,000 hectares are green.
Citrus and greenhouse vegetables, much of it grown for export. That green does not come from
the sky. It is pumped out of the ground.

![The irrigated Souss plain](figures/map_souss_use.png)

### 4. The cost, and the test that changed my answer

For the fourth map I asked whether that green is growing or shrinking. The data said it grew
46%, and I nearly wrote that down.

Then I remembered that 2026 was an unusually wet year. So I checked a patch of bare desert that
nobody irrigates. It had greened by 0.09 on its own, from rain alone. Most of what looked like
new farmland was just scrubland crossing my threshold after a wet winter.

Measured against that baseline the answer reverses. The land that was already farmland in 2018
is 0.25 lower in 2026. The established farms lost green even in a record wet year.

I wanted to know how sure I could be about that number, so I bootstrapped it. Pixels next to
each other are not independent, they belong to the same field, so I resampled 3.4 km blocks of
land rather than individual pixels. Two thousand resamples put the decline at 0.254, with a 95%
range from 0.245 to 0.263. Every single resample came out below zero, so the direction holds.
That range covers sampling uncertainty only. It does not cover the bigger question of why.

![Vegetation change on the Souss plain, 2018 to 2026](figures/map_souss_cost.png)

The brown rectangles are real fields.

I cannot tell you why from my own data, and I want to be clear about that. Either the wells are
failing, or open groves are being replaced by plastic greenhouses, which look dark from orbit.
Both would mean more pressure on the same groundwater. I built a test to separate them and it
did not work well enough to trust, so the repo says so.

Other people have gone further than I could. A study of this exact basin, published this year,
found that groundwater here has dropped by 20 to 65 metres over thirty years, as farmers moved
to alfalfa and fodder maize that need around 800 mm of water a cycle in a place that gets 99 mm
of rain. They call what they found the spectral illusion of crop health: the crisis is
"paradoxically masked from space" because irrigated fields can look healthy while the aquifer
below them empties.

That is a warning about the exact method I used. A vegetation index sees the canopy, not the
water table. Green is not proof that the water is there. It can be proof that somebody is
pumping harder. I have not changed any of my numbers to match their conclusion, and my data
still cannot prove why the farmland browned. But it is consistent with theirs, and I would
rather point you to the people who can answer it than pretend I already did. The papers are in
[REFERENCES.md](REFERENCES.md).

## The three times I was wrong

I think this matters more than any single map.

**I said the reservoir was vanishing.** It was not. I had stopped the data at 2024, at the
bottom of a drought. Extending it to 2026 showed it refilled past where it started, so I
rewrote the whole story.

**I said irrigation was growing.** It was not. A control test on bare desert showed the wet year
had greened everything, including land nobody farms. Once I subtracted that, the farms had lost
ground rather than gained it.

**I said the failing farms were greenhouses.** My test said 69% greenhouse. But when I checked
whether it could even tell its own reference examples apart, it managed 67.7%, barely better
than a coin flip. So the script reports the result as inconclusive instead of publishing a
number I could not defend.

Every map in this repo says what it cannot tell you, on the map itself.

## Does it hold together?

Four measurements that have nothing to do with each other all move the same way. That is how I
know I am not fooling myself.

| | Through the drought | 2025-26 |
|---|---|---|
| Reservoir surface | 98 down to 9 km2 | back to 125 km2 |
| Rainfall near Taroudant | recent decade about 31% below the 1990s | anomalously wet |
| Doukkala crop moisture | stressed | recovered |
| Argan vegetation, 25 years | declines through 2015-24 | rebounds |

![Rainfall near Taroudant since 1990](figures/fig_rainfall_trend.png)

Sentinel-2 only goes back to 2015, which is too short to prove a trend, so I pulled 25 years of
MODIS vegetation data to check the longer story. It drifts gently down, dips hard through the
drought, then rebounds. The land is stressed and rainfall-driven, not dying.

![25 years of vegetation on the argan slopes](figures/fig_modis_ndvi_trend.png)

I also classified the land cover around Taroudant from a spring Sentinel-2 scene, to see what is
actually on the ground.

![Land cover near Taroudant](figures/map_qgis_landcover.png)

## How it was built

Everything here comes from open data. No paid service, no Earth Engine account, no login.

The imagery is Sentinel-2, streamed from the Earth Search STAC catalogue with windowed reads so
I never download a whole scene. Terrain is the Copernicus GLO-30 DEM. Rainfall is NASA POWER.
Long-run vegetation is MODIS through ORNL. The national figures are World Bank.

Maps are made in QGIS with PyQGIS and in ArcGIS Pro with arcpy, at 300 dpi. The vector data
lives in a GeoPackage with a full attribute table, a data dictionary, an automated
quality-control report and an AutoCAD DXF export. There is spatial SQL over that geodatabase
with DuckDB, the rasters are published as validated Cloud Optimized GeoTIFFs and the vectors as
GeoParquet.

The scripts are grouped by what they do:

    src/fetch/         download the raw data (satellite, terrain, rainfall, World Bank)
    src/analysis/      the measurements: reservoir, rainfall, vegetation, crop stress,
                       the control tests and the confidence interval
    src/cartography/   the maps, built in QGIS and ArcGIS Pro
    src/figures/       charts, the timelapse, and the scrolling web story
    src/geodata/       the geodatabase, quality control, spatial SQL, and file formats

To reproduce it:

    pip install -r requirements.txt

    python src/fetch/fetch_worldbank.py
    python src/analysis/measure_reservoir.py
    python src/analysis/measure_rainshadow.py
    python src/analysis/measure_souss_change.py
    python src/analysis/bootstrap_ci.py
    python src/geodata/qa_qc.py

Then open QGIS and run the scripts in `src/cartography/` from its Python console. Every script
says at the top what it does and where it is uncertain.

## Read more

- [HOW-AND-WHY.md](HOW-AND-WHY.md), the reasoning behind every choice and what the analysis
  cannot say. This is the part I would most like you to read.
- [METADATA.md](METADATA.md), the data dictionary and coordinate systems.
- [QA_QC_REPORT.md](QA_QC_REPORT.md), the automated checks.
- [REFERENCES.md](REFERENCES.md), the published work this sits against.
- `storymap/index.html`, the same story as a scrolling web page.

Bouchra Daddaoui, 2026. Built with public data, in the hope it is useful to someone at home.

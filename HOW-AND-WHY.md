# How and why

*The thinking behind this project — not just what I did, but why I did it that way,
and what I know it can and cannot say. If you only read one file here, read this one.*

I did not want to make a project that looks impressive and means little. Anyone can
render a map now. What I wanted was to **understand** one water crisis well enough to
explain it honestly to someone who has never opened a GIS — and to be able to defend
every choice I made. This file is that reasoning.

## The question I actually asked

Not "can I make a map of Morocco's water?" but: **is the water crisis I keep hearing
about real, is it getting worse, and who does it fall on?** A question, not a
deliverable. Everything below is in service of answering it truthfully.

## Why I measured the reservoir from satellite instead of quoting a statistic

I could have written "Al Massira is nearly empty" and cited a headline. But I would not
have *known* it — I would have been repeating someone else. Measuring it myself, from
imagery anyone can download, is the difference between knowing and understanding. If I
am wrong, someone can rerun my code and catch me. That accountability is the point.

## Why surface area, and what it does *not* tell you

I measured the reservoir's **water surface area**, not its stored **volume**. That was a
deliberate, honest choice — and it has a limit I want to be clear about:

- **Volume** is what actually matters for supply, but computing it needs the shape of the
  reservoir floor (bathymetry), which is not openly available. I refuse to fake precision
  I don't have.
- **Surface area** is something I *can* measure transparently from every image.
- Crucially, area and volume are not proportional. As a reservoir drops, it narrows toward
  the deepest channel, so **volume falls even faster than area.** A 91% loss of surface is
  therefore a *conservative* signal — the volume story is very likely worse, not better.
  I would rather understate and be right than overstate and be caught.

## Why NDWI, and why an automatic (Otsu) threshold

- Water absorbs near-infrared light strongly and reflects green. The **Normalized
  Difference Water Index** (green − NIR) / (green + NIR) turns that physics into one number
  that is high over water and low over land. I used the 10 m green and NIR bands so the
  shoreline stays sharp.
- I did **not** draw the water/land line at a fixed value like NDWI = 0. That looks
  rigorous but is fragile: haze, sun angle, and sediment shift the histogram from year to
  year, so a fixed cutoff quietly measures different things in different images. Instead I
  used **Otsu's method**, which finds the threshold that best separates the two peaks *in
  each image's own histogram*. It adapts to the scene, and it is reproducible — no hand
  tuning, no eyeballing. Understanding *why fixed thresholds fail* is the whole reason I
  chose the adaptive one.

## Why dry-season images, and why the same tile every year

I compared **one least-cloudy dry-season image (Aug–Oct) per year**, always from the same
Sentinel-2 tile. This is about comparing like with like. The reservoir naturally rises and
falls within a year; if I mixed spring and autumn images I would be measuring the *season*,
not the *trend*. The dry-season low is also the honest moment — it is when scarcity bites.

## Why I cloud-masked, and why 2017 is the start

- Clouds and their shadows get misread as land or water, so I excluded them using the
  scene's own classification band. An unmasked cloud could invent or erase a lake.
- The series starts in **2017**, not earlier, because that is when Sentinel-2 reached full
  operational coverage. 2016 simply doesn't have reliable dry-season scenes here. That is a
  data limit I'm naming out loud — not a start date I picked to make the story worse.

## Why I kept the 2025 recovery in

The reservoir partly refilled after the wetter 2024–25 winter — from ~9 to ~25 km². Leaving
that out would have made a scarier chart and a dishonest one. It also *teaches* something
real: the system responds to rain, which is exactly why the solutions section is about
managing demand, not just praying for it. **Honesty and understanding are the same thing
here.** A story that can't admit a good year can't be trusted about the bad ones.

## Why I made it about people, not a reservoir

A shrinking blue polygon is easy to scroll past. So I asked the harder question: *who is on
the other end of this pipe?* The answer — 7.7 million people in one region, 96,000 hectares
of farmland, a protected wetland — is what turns a measurement into a reason to care. This
is the part I care about most, and the part no algorithm handed me: deciding that the point
of the map was never the map.

## What I know this project is *not*

Naming limits is how I show I understand my own work:

- It measures **surface area**, a proxy for storage — not volume, and not water quality.
- Al Massira is **one of several** sources for the region; I don't claim it is the only tap.
- The national reservoir fill-rate figures are **reported by authorities/press**, kept in a
  separate, clearly-labelled file — not something I measured.
- It is a **personal open-data project**, not peer-reviewed science. Where I lean on
  published research, I say so in [REFERENCES.md](REFERENCES.md).

## What I would do next

Bring in radar (Sentinel-1), which sees through cloud, to get water extent year-round;
pair the surface trend with rainfall and snow data to separate drought from over-use; and,
if bathymetry ever became available, convert area to volume. But I would only add
complexity that answers a real question — not to look sophisticated.

---

*Written by Bouchra Daddaoui. If you're reading this as part of my application: I would be
glad to walk you through any decision here in person. Understanding it is the point.*

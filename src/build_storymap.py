# -*- coding: utf-8 -*-
"""Build the 'Morocco's Vanishing Water' scrollytelling StoryMap as a
self-contained HTML file with all images embedded as data URIs."""
import base64
from io import BytesIO
from pathlib import Path
from PIL import Image

FIG = Path(r"C:/Users/BOUCHRA/Projects/morocco-water-stress/figures")
OUT = Path(r"C:/Users/BOUCHRA/Projects/morocco-water-stress/storymap/index.html")


def datauri(im, fmt="JPEG", quality=82):
    buf = BytesIO()
    if fmt == "JPEG":
        im = im.convert("RGB")
        im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        mime = "jpeg"
    else:
        im.save(buf, "PNG", optimize=True)
        mime = "png"
    return f"data:image/{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def load(name, maxw, fmt="JPEG", quality=82, crop=None):
    im = Image.open(FIG / name)
    if crop:
        im = im.crop(crop)
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    return datauri(im, fmt, quality)


# hero = satellite map region cropped out of the finished A3 layout (no panel/title)
# layout 4960x3507; map item x=8,y=30,w=292,h=258 mm on a 420x297 page
sx, sy = 4960 / 420, 3507 / 297
hero_crop = (int(8 * sx), int(30 * sy), int((8 + 292) * sx), int((30 + 258) * sy))

IMG = {
    "hero": load("map_al_massira_layout.png", 1900, "JPEG", 80, crop=hero_crop),
    "sat": load("map_al_massira_layout.png", 1700, "JPEG", 84),
    "grid": load("fig7_reservoir_masks_grid.png", 1600, "JPEG", 85),
    "series": load("fig6_reservoir_area_timeseries.png", 1400, "JPEG", 88),
    "community": load("map_communities_al_massira.png", 1700, "JPEG", 84),
    "percapita": load("fig1_percapita_decline.png", 1300, "JPEG", 88),
    "people": load("fig2_resource_vs_people.png", 1300, "JPEG", 88),
    "agri": load("fig3_agriculture_share.png", 1000, "JPEG", 88),
    "journey": load("map_water_journey.png", 1700, "JPEG", 84),
    "tc2017": load("truecolor_2017.jpg", 1400, "JPEG", 85),
    "tc2024": load("truecolor_2024.jpg", 1400, "JPEG", 85),
    "argan": load("map_argan_country.png", 1700, "JPEG", 86),
}

# the animation must stay a GIF (embed raw bytes, not re-encoded)
IMG["gif"] = "data:image/gif;base64," + base64.b64encode(
    (FIG / "reservoir_timelapse.gif").read_bytes()).decode()

total_kb = sum(len(v) for v in IMG.values()) / 1024
print(f"embedded {len(IMG)} images, ~{total_kb:.0f} KB base64")

HTML = f"""<title>Morocco's Vanishing Water</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{
  --bg:#12100d; --bg2:#191510; --surface:#211c15; --surface2:#2a241b;
  --text:#efe7d8; --muted:#a99a83; --faint:#7d715f;
  --water:#39aecb; --water-deep:#1c7994; --earth:#cd8a52; --crisis:#e5573f;
  --line:rgba(239,231,216,.14); --line2:rgba(239,231,216,.08);
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,"Times New Roman",serif;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{
  margin:0; background:var(--bg); color:var(--text);
  font-family:var(--sans); line-height:1.7;
  font-size:clamp(17px,1.05vw + 14px,20px); -webkit-font-smoothing:antialiased;
}}
img{{max-width:100%; display:block}}
.wrap{{max-width:820px; margin:0 auto; padding:0 24px}}
.eyebrow{{
  font-family:var(--mono); font-size:.72rem; letter-spacing:.28em;
  text-transform:uppercase; color:var(--earth); margin:0 0 1.1rem;
}}
h1,h2,h3{{font-family:var(--serif); font-weight:600; text-wrap:balance; line-height:1.08}}
h2{{font-size:clamp(2rem,4.2vw,3.2rem); margin:0 0 1.3rem; letter-spacing:-.01em}}
h3{{font-size:clamp(1.3rem,2.4vw,1.7rem); margin:2.4rem 0 .6rem}}
p{{margin:0 0 1.25rem}}
.lede{{font-size:1.22em; color:var(--text)}}
.muted{{color:var(--muted)}}
strong{{color:#fff; font-weight:600}}

/* hero */
.hero{{position:relative; min-height:100svh; display:flex; align-items:flex-end;
  overflow:hidden; border-bottom:1px solid var(--line)}}
.hero__img{{position:absolute; inset:0; background-size:cover; background-position:center;
  transform:scale(1.06)}}
.hero__scrim{{position:absolute; inset:0;
  background:linear-gradient(180deg,rgba(18,16,13,.55) 0%,rgba(18,16,13,.2) 35%,rgba(18,16,13,.82) 82%,var(--bg) 100%)}}
.hero__in{{position:relative; z-index:2; width:100%; padding:0 0 8vh}}
.hero h1{{font-size:clamp(3rem,9vw,6.4rem); margin:.2em 0 .3em; letter-spacing:-.02em; text-shadow:0 2px 30px rgba(0,0,0,.5)}}
.hero .kicker{{font-family:var(--mono); font-size:.78rem; letter-spacing:.3em; text-transform:uppercase; color:var(--water)}}
.hero .sub{{font-family:var(--serif); font-style:italic; font-size:clamp(1.2rem,2.6vw,1.7rem); color:var(--text); max-width:30ch; margin:.2em 0 0}}
.scrollcue{{margin-top:2.4rem; font-family:var(--mono); font-size:.72rem; letter-spacing:.22em; text-transform:uppercase; color:var(--muted); display:flex; align-items:center; gap:.7rem}}
.scrollcue::before{{content:""; width:1px; height:34px; background:linear-gradient(var(--water),transparent); display:inline-block}}

/* sections */
section{{padding:clamp(4.5rem,11vh,9rem) 0}}
.section--tint{{background:var(--bg2)}}
.figure{{margin:2.2rem 0 .4rem}}
.figure img{{width:100%; border-radius:6px; border:1px solid var(--line); box-shadow:0 24px 60px -30px rgba(0,0,0,.7)}}
.cap{{font-family:var(--mono); font-size:.74rem; color:var(--faint); margin:.7rem 2px 0; letter-spacing:.02em}}

/* full-bleed image band */
.band{{position:relative; min-height:88svh; display:flex; align-items:center;
  background-size:cover; background-position:center; border-top:1px solid var(--line); border-bottom:1px solid var(--line)}}
.band__scrim{{position:absolute; inset:0; background:linear-gradient(90deg,rgba(18,16,13,.9) 0%,rgba(18,16,13,.62) 45%,rgba(18,16,13,.25) 100%)}}
.band .wrap{{position:relative; z-index:2}}

/* stat */
.stat{{font-family:var(--mono); font-weight:600; line-height:.95;
  font-size:clamp(3.4rem,12vw,7rem); letter-spacing:-.02em}}
.stat--crisis{{color:var(--crisis)}} .stat--water{{color:var(--water)}} .stat--earth{{color:var(--earth)}}
.stat__cap{{font-family:var(--sans); font-size:1rem; color:var(--muted); max-width:34ch; margin:.9rem 0 0; line-height:1.6}}
.statrow{{display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:2.2rem; margin:2.6rem 0 1rem}}
.statrow .n{{font-family:var(--mono); font-weight:600; font-size:clamp(2.2rem,6vw,3.4rem); line-height:1}}
.statrow .l{{font-size:.92rem; color:var(--muted); margin-top:.5rem; line-height:1.5}}

.pull{{font-family:var(--serif); font-style:italic; font-size:clamp(1.5rem,3.4vw,2.3rem);
  line-height:1.3; color:var(--text); border-left:2px solid var(--earth);
  padding-left:1.2rem; margin:2.4rem 0}}

.reveal{{opacity:0; transform:translateY(22px); transition:opacity .9s ease, transform .9s ease}}
.reveal.in{{opacity:1; transform:none}}
@media (prefers-reduced-motion:reduce){{
  .reveal{{opacity:1; transform:none; transition:none}} html{{scroll-behavior:auto}}
  .hero__img{{transform:none}}
}}

/* before/after swipe */
.swipe{{position:relative; margin:2.2rem 0 .4rem; border-radius:6px; overflow:hidden;
  border:1px solid var(--line); box-shadow:0 24px 60px -30px rgba(0,0,0,.7); user-select:none; touch-action:none}}
.swipe img{{display:block; width:100%}}
.swipe__top{{position:absolute; inset:0}}
.swipe__handle{{position:absolute; top:0; bottom:0; left:50%; width:2px; background:#fff;
  box-shadow:0 0 0 1px rgba(0,0,0,.35); transform:translateX(-1px); pointer-events:none}}
.swipe__handle::after{{content:"\\2194"; position:absolute; top:50%; left:50%;
  transform:translate(-50%,-50%); width:38px; height:38px; border-radius:50%;
  background:#fff; color:#111; font-size:19px; line-height:38px; text-align:center;
  box-shadow:0 2px 10px rgba(0,0,0,.4)}}
.swipe__tag{{position:absolute; top:12px; font-family:var(--mono); font-size:.72rem;
  letter-spacing:.12em; text-transform:uppercase; color:#fff; background:rgba(0,0,0,.5);
  padding:4px 9px; border-radius:4px; z-index:3}}
.swipe__tag--l{{left:12px}} .swipe__tag--r{{right:12px}}
.swipe__range{{position:absolute; left:0; bottom:0; width:100%; margin:0; opacity:0; height:100%; cursor:ew-resize}}

footer{{background:#0d0b09; border-top:1px solid var(--line); padding:4rem 0 5rem; color:var(--muted)}}
footer a{{color:var(--water); text-decoration:none; border-bottom:1px solid var(--line2)}}
footer h3{{color:var(--text); margin-top:0}}
.src{{font-size:.86rem; line-height:1.9}}
.byline{{font-family:var(--mono); font-size:.76rem; letter-spacing:.16em; text-transform:uppercase; color:var(--faint); margin-top:2.4rem}}
</style>

<header class="hero">
  <div class="hero__img" style="background-image:url('{IMG['hero']}')"></div>
  <div class="hero__scrim"></div>
  <div class="hero__in"><div class="wrap">
    <p class="kicker">Morocco &middot; a water story, measured from space</p>
    <h1>Running Dry</h1>
    <p class="sub">My country is losing its water. So I went looking for it &mdash; from orbit.</p>
    <div class="scrollcue">Scroll</div>
  </div></div>
</header>

<section><div class="wrap reveal">
  <p class="eyebrow">The line we crossed</p>
  <h2>A country slipping into water scarcity</h2>
  <p class="lede">I grew up hearing that Morocco was dry. I did not know that, by the
  numbers, we had quietly crossed one of the lines hydrologists use to define a crisis.</p>
  <p>In 1961 each person in Morocco had about <strong>2,431 cubic metres</strong> of
  renewable freshwater a year. By 2022 that had fallen to <strong>777</strong> &mdash; below
  the international water-stress threshold of 1,000&nbsp;m&sup3;, and drifting toward the
  500&nbsp;m&sup3; mark that defines <em>absolute scarcity</em>. This is the whole story in
  one line, drawn straight from World Bank data.</p>
  <div class="figure"><img src="{IMG['percapita']}" alt="Renewable freshwater per person in Morocco, 1961 to 2022, falling below the water-stress line around 2000" loading="lazy">
    <p class="cap">Renewable internal freshwater per capita. Source: World Bank Open Data.</p></div>
</div></section>

<section class="section--tint"><div class="wrap reveal">
  <p class="eyebrow">Why it is happening</p>
  <h2>The water didn&rsquo;t shrink. We multiplied.</h2>
  <p>Here is what surprised me most. Morocco&rsquo;s total renewable freshwater has stayed
  almost flat &mdash; around <strong>29 billion cubic metres a year</strong> &mdash; for six
  decades. What changed is the number of people sharing it: the population roughly
  <strong>tripled</strong>, from about 12 to 38 million. Add drought, which shrinks the
  usable share still further, and the arithmetic becomes unforgiving.</p>
  <div class="figure"><img src="{IMG['people']}" alt="Flat water supply against tripling population, 1961 to 2022" loading="lazy">
    <p class="cap">Fixed water, rising population. Source: World Bank Open Data.</p></div>
  <h3>And most of it goes to one place</h3>
  <p>About <strong>88%</strong> of all the freshwater Morocco withdraws goes to
  agriculture &mdash; often to thirsty, export-oriented crops. Water stress here is
  inseparable from farming, food, and rural livelihoods.</p>
  <div class="figure"><img src="{IMG['agri']}" alt="Agriculture uses 88 percent of Morocco's freshwater withdrawals" loading="lazy" style="max-width:520px;margin-inline:auto">
    <p class="cap" style="text-align:center">Source: World Bank Open Data.</p></div>
</div></section>

<section><div class="wrap reveal">
  <p class="eyebrow">Where the water begins</p>
  <h2>It all starts in the mountains</h2>
  <p>Al&nbsp;Massira does not make water &mdash; it catches it. Every drop begins as winter
  snow and rain on the <strong>Middle Atlas</strong>, drains down the Oum&nbsp;Er-Rbia, and
  collects behind the dam. I built this shaded-relief map from open elevation data to show
  that journey: the pale peaks rise above 3,000&nbsp;m, and the water runs downhill from
  there to the reservoir, the cities, and the fields.</p>
  <div class="figure"><img src="{IMG['journey']}" alt="Shaded-relief map of the Oum Er-Rbia headwaters, Middle Atlas terrain feeding the Al Massira reservoir" loading="lazy">
    <p class="cap">Shaded relief + hypsometric tint from the Copernicus 30&nbsp;m DEM. Made in QGIS.</p></div>
</div></section>

<div class="band" style="background-image:url('{IMG['hero']}')">
  <div class="band__scrim"></div>
  <div class="wrap reveal">
    <p class="eyebrow">From statistic to place</p>
    <h2 style="max-width:16ch">So I stopped reading numbers and looked from space.</h2>
    <p class="lede" style="max-width:40ch">To see what scarcity really means, I followed one
    reservoir &mdash; Al&nbsp;Massira &mdash; through nine years of satellite imagery.</p>
  </div>
</div>

<section><div class="wrap reveal">
  <p class="eyebrow">The measurement</p>
  <h2>Al Massira, vanishing</h2>
  <p>Al&nbsp;Massira is Morocco&rsquo;s second-largest reservoir. It sits on the
  Oum&nbsp;Er-Rbia river and sends water to Casablanca and to the farms of the Doukkala
  plain. I pulled every dry-season <strong>Sentinel-2</strong> image from 2017 to 2025,
  mapped the open water with a spectral index (NDWI) and an automatic threshold, and
  measured the surface area myself. No estimates &mdash; a measurement.</p>
  <div class="figure"><img src="{IMG['gif']}" alt="Animated timelapse of the Al Massira reservoir shrinking from 2017 to 2025" loading="lazy">
    <p class="cap">Nine dry seasons: the reservoir draining against the pale outline of its 2017 pool. Every frame is a real Sentinel-2 measurement.</p></div>
  <div class="statrow">
    <div><div class="n" style="color:var(--water)">98 km&sup2;</div><div class="l">water surface in 2017</div></div>
    <div><div class="n" style="color:var(--crisis)">9 km&sup2;</div><div class="l">what remained in 2024</div></div>
    <div><div class="n" style="color:var(--earth)">Ramsar</div><div class="l">a wetland of international importance, drying out</div></div>
  </div>
  <div class="figure"><img src="{IMG['grid']}" alt="Year by year satellite water masks of Al Massira reservoir shrinking from 2017 to 2025" loading="lazy">
    <p class="cap">Water extent each dry season, measured from Sentinel-2. The reservoir shrinks before your eyes.</p></div>
  <p class="stat stat--crisis" style="margin-top:2.5rem">&minus;91%</p>
  <p class="stat__cap">of Al&nbsp;Massira&rsquo;s water surface, lost between 2017 and 2024 &mdash; before a
  partial recovery after the wetter 2024&ndash;25 winter. Honesty matters: the rains did come back, a little.</p>
  <div class="figure"><img src="{IMG['series']}" alt="Time series of Al Massira water surface area, 2017 to 2025" loading="lazy">
    <p class="cap">Nine dry seasons of measured water-surface area.</p></div>
  <div class="figure"><img src="{IMG['sat']}" alt="High-resolution QGIS map of Al Massira: 2017 shoreline versus 2024 water over satellite imagery" loading="lazy">
    <p class="cap">The 2017 shoreline (cyan) over what was left in 2024 (blue). The pale ground between them is exposed lakebed. Made in QGIS.</p></div>

  <h3>See it yourself: drag from 2017 to 2024</h3>
  <p>This is the raw satellite view &mdash; no analysis, just the true colour of the land.
  Drag the handle across and watch the dark water turn to bare, cracked lakebed.</p>
  <div class="swipe" id="swipe">
    <img src="{IMG['tc2024']}" alt="Al Massira in 2024, nearly empty (Sentinel-2 true colour)">
    <div class="swipe__top" id="swipeTop"><img src="{IMG['tc2017']}" alt="Al Massira in 2017, full (Sentinel-2 true colour)"></div>
    <div class="swipe__handle" id="swipeHandle"></div>
    <span class="swipe__tag swipe__tag--l">2017 &middot; full</span>
    <span class="swipe__tag swipe__tag--r">2024 &middot; empty</span>
    <input class="swipe__range" id="swipeRange" type="range" min="0" max="100" value="50" aria-label="Reveal 2017 versus 2024">
  </div>
  <p class="cap">True-colour Sentinel-2, same footprint both years. Drag to compare.</p>
</div></section>

<section class="section--tint"><div class="wrap reveal">
  <p class="eyebrow">Who this is really about</p>
  <h2>A reservoir is a community</h2>
  <p>A shrinking blue shape on a map is easy to scroll past. So here is what it holds. The
  water behind Al&nbsp;Massira reaches the <strong>Casablanca-Settat region</strong> &mdash;
  home to <strong>7.7&nbsp;million people</strong> in the 2024 census &mdash; and irrigates
  roughly <strong>96,000&nbsp;hectares</strong> of Doukkala farmland. When the reservoir
  falls, it is their taps, their harvests, and a protected wetland&rsquo;s birds that feel it first.</p>
  <div class="figure"><img src="{IMG['community']}" alt="Map of the communities and farmland that depend on the Al Massira reservoir" loading="lazy">
    <p class="cap">Who depends on Al&nbsp;Massira. Population: HCP Morocco 2024 census. Irrigation: ORMVAD. Made in QGIS.</p></div>
  <p class="pull">This is why the map matters to me. It is not a foreign crisis on a
  screen. It is the water my own country runs on.</p>
</div></section>

<section><div class="wrap reveal">
  <p class="eyebrow">Where I&rsquo;m from</p>
  <h2>And where everyone goes</h2>
  <p>I did not start caring about water in the north. I started caring about it at home, in
  the <strong>south</strong> &mdash; the Souss valley and the Anti-Atlas, where I am from. It
  is a dry land between two mountain ranges, and in my lifetime it has grown drier. Where
  families once farmed, there is now only enough water to drink and to wash. The one tree that
  still holds on is the argan, because it can live on almost nothing.</p>
  <div class="figure"><img src="{IMG['argan']}" alt="Shaded-relief map of the Souss valley and the Anti-Atlas, the author's home region" loading="lazy">
    <p class="cap">Home: the Souss valley between the High Atlas and the Anti-Atlas. Copernicus DEM, rendered in Python.</p></div>
  <p>When the water fails, people do the one thing the land will no longer let them do: they
  leave. That is the quiet question under all of this &mdash; not only how much water is left,
  but <em>where everyone goes</em> when a place can no longer hold them. The people losing
  their homes did the least to warm the climate. To me, that is what environmental justice
  means: not an abstraction, but the difference between a family staying and a family leaving.</p>
</div></section>

<section><div class="wrap reveal">
  <p class="eyebrow">What can still be done</p>
  <h2>Scarcity is a choice, not only a fate</h2>
  <p>Morocco is not standing still. The response runs from the very large to the very small,
  and the honest debate is whether supply can outrun demand &mdash; or whether the harder
  question is <em>what a dry country chooses to grow.</em></p>
  <div class="statrow">
    <div><div class="n" style="font-size:clamp(1.4rem,3.2vw,1.9rem);color:var(--water)">Desalination</div><div class="l">new plants, including one of Africa&rsquo;s largest planned for Casablanca</div></div>
    <div><div class="n" style="font-size:clamp(1.4rem,3.2vw,1.9rem);color:var(--water)">Drip irrigation</div><div class="l">cutting the water lost in the fields that use most of it</div></div>
    <div><div class="n" style="font-size:clamp(1.4rem,3.2vw,1.9rem);color:var(--water)">Recharge &amp; reuse</div><div class="l">refilling aquifers and reusing treated water</div></div>
  </div>
  <p>Every one of these is a mapping problem before it is an engineering one: where the water
  is, where it goes, who needs it most. That is the work I want to do.</p>
</div></section>

<section class="section--tint"><div class="wrap reveal">
  <p class="eyebrow">Why I made this</p>
  <h2>A map is a way of saying: look closer</h2>
  <p>I am from the south of Morocco, where the mountains meet the desert &mdash; a place that
  is drying out. In my hometown, water is now only for drinking and washing; the farms are
  gone, and people are leaving. The one tree that still holds on is the argan, because it can
  live on almost nothing.</p>
  <p>That is why I made this. Al&nbsp;Massira lies far to the north, but it let me prove I
  could measure a water crisis <strong>honestly</strong>, from open data anyone can check. The
  reason behind it is closer to home: I want to understand how our water is changing, and help
  the communities losing it be seen in time. Researchers here &mdash; at UM6P and beyond &mdash;
  are asking the same questions. I wanted to add something small but open: a project anyone can
  download, rerun, and build on.</p>
  <p>If a map makes one more person care about a place they will never visit, it has done its
  job. That is the work I want to spend my life on.</p>
</div></section>

<footer><div class="wrap">
  <h3>About this story</h3>
  <p class="muted">I built this to make a slow, invisible crisis visible &mdash; using only
  open data and reproducible code. Every figure here can be regenerated from scratch.</p>
  <p class="src muted">
  <strong style="color:var(--text)">Data &amp; methods.</strong><br>
  Freshwater &amp; population &mdash; World Bank Open Data (CC&nbsp;BY&nbsp;4.0).<br>
  Reservoir surface &mdash; measured from Sentinel-2 L2A (Copernicus) via Earth Search, NDWI&nbsp;+&nbsp;Otsu, cloud-masked.<br>
  Boundaries &mdash; geoBoundaries (CC&nbsp;BY&nbsp;4.0). Population &mdash; HCP Morocco 2024 census. Irrigation &mdash; ORMVAD.<br>
  Maps &mdash; QGIS / PyQGIS. Basemaps &mdash; Esri World Imagery, CARTO, OpenTopoMap.<br>
  Code &amp; full pipeline: <a href="https://github.com/Bouchra159/morocco-water-stress">github.com/Bouchra159/morocco-water-stress</a>
  </p>
  <p class="src muted" style="margin-top:1.4rem">
  <strong style="color:var(--text)">In dialogue with research.</strong> This project corroborates and builds on published work, including:<br>
  &middot; <a href="https://www.nature.com/articles/s41598-025-06240-1">Monitoring water crisis from space across a Mediterranean region</a> &mdash; <em>Scientific Reports</em>, 2025<br>
  &middot; <a href="https://www.researchgate.net/publication/367763659">Temporal evolution of the water retention of Al&nbsp;Massira Dam</a> &mdash; 2023<br>
  &middot; <a href="https://doi.org/10.3390/rs17020281">Drought propagation in the Oum&nbsp;Er-Rbia watershed</a> &mdash; <em>Remote Sensing</em>, 2025
  </p>
  <p class="byline">Analysis, cartography &amp; words &mdash; Bouchra Daddaoui &middot; 2026</p>
</div></footer>

<script>
const io=new IntersectionObserver((es)=>{{es.forEach(e=>{{if(e.isIntersecting){{e.target.classList.add('in');io.unobserve(e.target)}}}})}},{{threshold:.14}});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
const _sr=document.getElementById('swipeRange');
if(_sr){{
  const _top=document.getElementById('swipeTop'), _h=document.getElementById('swipeHandle');
  const _u=v=>{{_top.style.clipPath='inset(0 '+(100-v)+'% 0 0)'; _h.style.left=v+'%';}};
  _sr.addEventListener('input',e=>_u(e.target.value)); _u(50);
}}
</script>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
kb = len(HTML.encode("utf-8")) / 1024
print(f"wrote {OUT}  ({kb:.0f} KB)")

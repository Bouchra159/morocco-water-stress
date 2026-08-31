"""
measure_groundwater.py
Trying to separate groundwater from everything else.

GRACE weighs ALL the water in a region at once: snow, rivers, soil moisture and
groundwater in a single number. That is why the previous script could only say
"the region is losing water" and not "the aquifer is being drained". This is the
standard way to go one step further.

    groundwater anomaly  =  total water storage (GRACE)
                            minus soil moisture (a land surface model)

Whatever is left after you remove the water held in the soil is mostly what is
underneath it. Here the soil term is ERA5-Land, sampled through Open-Meteo, which
needs no account, in keeping with the rest of this project.

HOW MUCH TO TRUST THIS
  * The soil term is a MODEL, not a measurement. Nobody has put a probe in the
    ground across the Souss. Every error in that model lands in the groundwater
    estimate, because it is a subtraction.
  * GRACE's footprint is a few hundred kilometres, wider than either basin, so
    this is the region a basin sits in rather than the basin itself.
  * Snow and surface water are ignored. In the Souss that is reasonable, it
    barely snows. For the Oum Er-Rbia, the Atlas snowpack and the reservoir
    itself are real terms I am not accounting for, so read that basin's number
    more cautiously.
  * The result is an anomaly against a baseline, not an absolute volume, and it
    cannot be converted into metres of water-table drop without knowing the
    aquifer's specific yield.

So: indicative, not authoritative. It is the difference between "the region is
drying" and "the drying looks like it is coming from underground", which is a
real step, but it is not a well record.

Outputs: data/processed/groundwater.csv, figures/fig_groundwater.png
"""
from __future__ import annotations

import os
import pathlib
import time

import numpy as np
import pandas as pd
import requests


def _repo_root():
    try:
        return pathlib.Path(__file__).resolve().parents[2]
    except NameError:
        return pathlib.Path(os.environ.get("MOROCCO_REPO", os.getcwd()))


ROOT = _repo_root()
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"
GRACE_CSV = PROCESSED / "grace_storage.csv"
CACHE = PROCESSED / "soil_moisture.csv"

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# ERA5-Land soil layers and their thickness in cm
LAYERS = [("soil_moisture_0_to_7cm", 7.0),
          ("soil_moisture_7_to_28cm", 21.0),
          ("soil_moisture_28_to_100cm", 72.0),
          ("soil_moisture_100_to_255cm", 155.0)]

# a few sample points inside each basin, matching the GRACE boxes
POINTS = {
    "Souss-Massa (my region)": [(30.4, -9.2), (30.1, -8.3), (29.6, -8.9), (30.7, -8.0)],
    "Oum Er-Rbia (Al Massira)": [(32.5, -7.6), (32.9, -6.8), (32.2, -8.2), (33.1, -6.4)],
}

START, END = "2002-04-01", "2026-06-30"
BASELINE = ("2004-01-01", "2009-12-31")     # common reference window for both series
CHUNK_YEARS = 6


def fetch_point(lat, lon):
    """Monthly soil-column water (cm) at one point, from ERA5-Land."""
    monthly = []
    start = pd.Timestamp(START)
    end = pd.Timestamp(END)
    while start < end:
        stop = min(start + pd.DateOffset(years=CHUNK_YEARS) - pd.Timedelta(days=1), end)
        params = {"latitude": lat, "longitude": lon,
                  "start_date": start.date().isoformat(),
                  "end_date": stop.date().isoformat(),
                  "hourly": ",".join(n for n, _ in LAYERS),
                  "models": "era5_land"}
        for attempt in range(4):
            try:
                r = requests.get(ARCHIVE, params=params, timeout=180)
                j = r.json()
                if "hourly" in j:
                    break
                print(f"      {j.get('reason', 'no data')}")
            except Exception as e:
                print(f"      retry after {type(e).__name__}")
            time.sleep(3 * (attempt + 1))
        else:
            start = stop + pd.Timedelta(days=1)
            continue

        h = j["hourly"]
        df = pd.DataFrame({n: h[n] for n, _ in LAYERS},
                          index=pd.to_datetime(h["time"]))
        # volumetric fraction times layer thickness = cm of water in that layer
        col = sum(df[n].astype(float) * t for n, t in LAYERS)
        monthly.append(col.resample("MS").mean())
        start = stop + pd.Timedelta(days=1)

    if not monthly:
        return None
    return pd.concat(monthly).sort_index()


def soil_series():
    if CACHE.exists() and os.environ.get("SOIL_REFETCH") != "1":
        print(f"using cached {CACHE.name} (set SOIL_REFETCH=1 to redo)")
        d = pd.read_csv(CACHE, parse_dates=["date"])
        return d

    rows = []
    for region, pts in POINTS.items():
        print(f"\n{region}")
        series = []
        for lat, lon in pts:
            print(f"   sampling {lat}, {lon}")
            s = fetch_point(lat, lon)
            if s is not None:
                series.append(s)
        if not series:
            continue
        avg = pd.concat(series, axis=1).mean(axis=1)
        for t, v in avg.items():
            rows.append({"region": region, "date": t, "soil_cm": round(float(v), 3)})
    d = pd.DataFrame(rows)
    d.to_csv(CACHE, index=False)
    print(f"\nwrote {CACHE.relative_to(ROOT)}")
    return d


def anomaly(s, dates, lo, hi):
    """Centre a series on its mean over the baseline window."""
    m = (dates >= pd.Timestamp(lo)) & (dates <= pd.Timestamp(hi))
    if m.sum() == 0:
        return s - np.nanmean(s)
    return s - np.nanmean(s[m])


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    if not GRACE_CSV.exists():
        print("run src/analysis/measure_grace.py first")
        return

    grace = pd.read_csv(GRACE_CSV, parse_dates=["date"])
    grace["lwe_cm"] = pd.to_numeric(grace["lwe_cm"], errors="coerce")
    soil = soil_series()
    soil["date"] = pd.to_datetime(soil["date"])

    out, trends = [], {}
    for region in POINTS:
        g = grace[grace.region == region].dropna(subset=["lwe_cm"]).copy()
        s = soil[soil.region == region].copy()
        if g.empty or s.empty:
            continue
        # GRACE is monthly-ish; snap both to month start and join
        g["m"] = g["date"].values.astype("datetime64[M]")
        s["m"] = s["date"].values.astype("datetime64[M]")
        j = g.merge(s[["m", "soil_cm"]], on="m", how="inner").sort_values("m")
        if len(j) < 24:
            print(f"{region}: only {len(j)} overlapping months, skipping")
            continue

        dates = pd.to_datetime(j["m"])
        tws = anomaly(np.asarray(j["lwe_cm"], float), dates, *BASELINE)
        sms = anomaly(np.asarray(j["soil_cm"], float), dates, *BASELINE)
        gws = tws - sms

        yrs = np.asarray((dates - dates.min()).dt.days / 365.25, dtype=float)
        tr = {k: float(np.polyfit(yrs, v, 1)[0]) for k, v in
              (("total", tws), ("soil", sms), ("ground", gws))}
        trends[region] = tr
        print(f"\n{region}   ({len(j)} months, {dates.min():%Y}-{dates.max():%Y})")
        print(f"   total water storage   {tr['total']:+.3f} cm/yr")
        print(f"   soil moisture         {tr['soil']:+.3f} cm/yr")
        print(f"   groundwater, implied  {tr['ground']:+.3f} cm/yr")
        share = 100 * tr["ground"] / tr["total"] if tr["total"] else float("nan")
        print(f"   -> {share:.0f}% of the loss is left after removing soil moisture")

        for d, a, b, c in zip(dates, tws, sms, gws):
            out.append({"region": region, "date": d.date().isoformat(),
                        "total_cm": round(float(a), 3), "soil_cm": round(float(b), 3),
                        "groundwater_cm": round(float(c), 3)})

    if not out:
        print("no overlapping data")
        return
    pd.DataFrame(out).to_csv(PROCESSED / "groundwater.csv", index=False)
    print(f"\nwrote data/processed/groundwater.csv ({len(out)} rows)")

    # ---- figure ------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("seaborn-v0_8-whitegrid")

    d = pd.DataFrame(out)
    d["date"] = pd.to_datetime(d["date"])
    regions = [r for r in POINTS if r in trends]
    fig, axes = plt.subplots(len(regions), 1, figsize=(10, 4.2 * len(regions)), sharex=True)
    if len(regions) == 1:
        axes = [axes]

    for ax, region in zip(axes, regions):
        r = d[d.region == region].sort_values("date")
        gap = r["date"].diff().dt.days > 200
        for col, lab, c in (("total_cm", "total water (GRACE)", "tab:blue"),
                            ("soil_cm", "soil moisture (ERA5-Land)", "tab:orange"),
                            ("groundwater_cm", "what is left after soil", "tab:brown")):
            v = r[col].copy()
            v[gap] = np.nan
            ax.plot(r["date"], v, lw=1.3, color=c,
                    label=f"{lab}   ({trends[region][col.split('_')[0].replace('groundwater','ground')]:+.2f} cm/yr)")
        ax.axhline(0, color="gray", lw=0.8)
        ax.set_title(region, fontsize=11)
        ax.set_ylabel("anomaly (cm of water)")
        ax.legend(fontsize=8, loc="lower left")

    axes[-1].set_xlabel("Year")
    fig.suptitle("Taking the soil out of the gravity signal\n"
                 "what is left is mostly groundwater", y=0.99)
    fig.tight_layout()
    fig.savefig(FIG / "fig_groundwater.png", dpi=150)
    plt.close(fig)
    print("wrote figures/fig_groundwater.png")
    print("\nreminder: the soil term is a model. This is indicative, not a well record.")


if __name__ == "__main__":
    main()

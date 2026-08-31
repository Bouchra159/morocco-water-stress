"""
measure_grace.py
Weighing the water that is left, from orbit.

Everything else in this project measures the surface: the shine of a reservoir,
the green of a field. None of it can see the water underground, which is where
the Souss-Massa basin actually keeps most of what it uses. That is the hole in my
fourth map. I found that established farmland lost vegetation and could not tell
you whether the wells were failing.

GRACE and GRACE-FO can help. They are twin satellites that measure tiny changes
in Earth's gravity, and water is heavy enough to show up. Where water leaves a
region, gravity weakens very slightly. So the satellites can weigh the total
water in a basin without seeing it at all.

WHAT THIS CAN AND CANNOT TELL YOU
  * It measures TOTAL water storage: snow, surface water, soil moisture and
    groundwater added together. It is not a groundwater measurement on its own.
    Separating groundwater needs a land surface model (GLDAS) subtracted from it,
    which I have not done here.
  * The footprint is coarse, a few hundred kilometres. Souss-Massa is smaller
    than that, so this is the regional signal the basin sits inside, not a
    measurement of the basin alone. Read it as context, not as a local number.
  * There is a gap in 2017 and 2018 between the two missions. It is left empty
    rather than interpolated across.

Data: CSR GRACE/GRACE-FO RL06.03 mascons (University of Texas), public download,
no account needed. Units are centimetres of equivalent water thickness, as an
anomaly against the mission mean.

Outputs: data/processed/grace_storage.csv, figures/fig_grace_storage.png
"""
from __future__ import annotations

import os
import pathlib

import numpy as np
import pandas as pd


def _repo_root():
    try:
        return pathlib.Path(__file__).resolve().parents[2]
    except NameError:
        return pathlib.Path(os.environ.get("MOROCCO_REPO", os.getcwd()))


ROOT = _repo_root()
NC = ROOT / "data" / "raw" / "grace" / "CSR_mascons_RL0603.nc"
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

# regions to sample: (name, lon_min, lat_min, lon_max, lat_max)
REGIONS = [
    ("Souss-Massa (my region)", -9.9, 29.2, -7.6, 31.1),
    ("Oum Er-Rbia (Al Massira)", -8.6, 32.0, -6.2, 33.4),
]


def decode_time(time_da):
    """Turn the file's time axis into real dates.

    These files label the units attribute "Units" with a capital U, which is not
    the CF spelling, so xarray leaves the axis as raw floats. Reading those as if
    they were already timestamps silently collapses every month onto 1970-01-01,
    which is exactly the sort of error that produces a confident, meaningless
    trend. So decode it explicitly instead.
    """
    units = time_da.attrs.get("units") or time_da.attrs.get("Units") or ""
    values = np.asarray(time_da.values, dtype=float)
    if "since" in units:
        origin = pd.Timestamp(units.split("since", 1)[1].strip().replace("Z", ""))
        unit = units.split("since", 1)[0].strip().lower()
        step = {"days": "D", "hours": "h", "seconds": "s"}.get(unit, "D")
        return pd.to_datetime(origin) + pd.to_timedelta(values, unit=step)
    return pd.to_datetime(time_da.values)


def main() -> None:
    import xarray as xr

    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    if not NC.exists():
        print(f"missing {NC}. Download it first (see the docstring).")
        return

    ds = xr.open_dataset(NC)
    var = next((v for v in ("lwe_thickness", "lwe_thickness_mascon", "lwe")
                if v in ds.variables), None)
    if var is None:
        var = [v for v in ds.data_vars if ds[v].ndim == 3][0]
    da = ds[var]
    lon_name = "lon" if "lon" in da.dims else "longitude"
    lat_name = "lat" if "lat" in da.dims else "latitude"
    print(f"variable: {var}   dims: {dict(da.sizes)}")

    # CSR mascons are on a 0-360 longitude grid
    lons = ds[lon_name].values
    shift = lons.max() > 180

    rows = []
    for name, lo0, la0, lo1, la1 in REGIONS:
        a, b = (lo0 % 360, lo1 % 360) if shift else (lo0, lo1)
        sel = da.sel({lon_name: slice(min(a, b), max(a, b)),
                      lat_name: slice(la0, la1)})
        if sel.sizes.get(lat_name, 0) == 0:            # descending latitude axis
            sel = da.sel({lon_name: slice(min(a, b), max(a, b)),
                          lat_name: slice(la1, la0)})
        ts = sel.mean(dim=[lon_name, lat_name], skipna=True)
        n_cells = sel.sizes.get(lon_name, 0) * sel.sizes.get(lat_name, 0)
        print(f"{name}: {n_cells} grid cells, {ts.sizes['time']} months")
        for t, v in zip(decode_time(ts["time"]), ts.values):
            rows.append({"region": name, "date": t.date().isoformat(),
                         "lwe_cm": None if np.isnan(v) else round(float(v), 3)})

    df = pd.DataFrame(rows)
    # gaps were stored as None, which leaves the column as object dtype and
    # makes the least-squares fit below fail; force it to real floats
    df["lwe_cm"] = pd.to_numeric(df["lwe_cm"], errors="coerce")
    df.to_csv(PROCESSED / "grace_storage.csv", index=False)
    print(f"wrote data/processed/grace_storage.csv ({len(df)} rows)")

    # ---- trend per region, over the common record --------------------------
    print("\ntrend in total water storage")
    trends = {}
    for name, *_ in REGIONS:
        d = df[(df.region == name) & df.lwe_cm.notna()].copy()
        d["date"] = pd.to_datetime(d["date"])
        yrs = np.asarray((d["date"] - d["date"].min()).dt.days / 365.25, dtype=float)
        vals = np.asarray(d["lwe_cm"], dtype=float)
        slope, intercept = np.polyfit(yrs, vals, 1)
        trends[name] = slope
        span = f"{d['date'].min():%Y} to {d['date'].max():%Y}"
        print(f"  {name:28s} {slope:+.2f} cm/yr   ({span}, n={len(d)})")

    # ---- figure, plain style ------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(10, 5))
    colours = {"Souss-Massa (my region)": "tab:brown",
               "Oum Er-Rbia (Al Massira)": "tab:blue"}
    for name, *_ in REGIONS:
        d = df[(df.region == name) & df.lwe_cm.notna()].copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d.sort_values("date")
        # break the line across the gap between the two missions
        gap = d["date"].diff().dt.days > 200
        seg = d.copy()
        seg.loc[gap, "lwe_cm"] = np.nan
        ax.plot(seg["date"], seg["lwe_cm"], lw=1.4, color=colours[name],
                label=f"{name}   ({trends[name]:+.2f} cm/yr)")
        yrs = np.asarray((d["date"] - d["date"].min()).dt.days / 365.25, dtype=float)
        s, i = np.polyfit(yrs, np.asarray(d["lwe_cm"], dtype=float), 1)
        ax.plot(d["date"], s * yrs + i, ls="--", lw=1.1,
                color=colours[name], alpha=0.75)

    ax.axhline(0, color="gray", lw=0.8)
    ax.set_ylabel("Water storage anomaly (cm of equivalent water)")
    ax.set_xlabel("Year")
    ax.set_title("Total water storage over Morocco's basins, measured by gravity\n"
                 "GRACE and GRACE-FO, 2002 to present (dashed = linear trend)")
    ax.legend(loc="lower left", fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "fig_grace_storage.png", dpi=150)
    plt.close(fig)
    print("wrote figures/fig_grace_storage.png")

    print("\nreminder: this is TOTAL water storage, not groundwater alone, and the")
    print("footprint is larger than either basin. It is regional context.")


if __name__ == "__main__":
    main()

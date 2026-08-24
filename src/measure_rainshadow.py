"""
measure_rainshadow.py
The rain shadow of the High Atlas — why the south (home) runs dry.

Inspired by National Geographic's "Precipitation Across Landscapes" lesson
(windward vs leeward / orographic rain shadow), but measured with real data:
annual rainfall sampled on a grid across the mountains from NASA POWER, then
interpolated into a precipitation surface. Atlantic moisture rains out on the
windward High Atlas in the north; the leeward Souss and Anti-Atlas in the south
sit in the rain shadow and fade toward the Sahara.

Outputs: data/processed/rainshadow_grid.csv,
         data/geo/precip_rainshadow.tif  (annual mm, EPSG:4326)
"""
from __future__ import annotations
import calendar
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
GEO = ROOT / "data" / "geo"
POWER = "https://power.larc.nasa.gov/api/temporal/climatology/point"
AOI = (-9.85, 30.1, -8.15, 31.9)          # inside the DEM, coast -> High Atlas
NLON, NLAT = 7, 8                          # sample grid (NASA POWER ~0.5 deg native)
RES = 0.02                                 # output raster ~2 km


def annual_precip(lon: float, lat: float) -> float | None:
    try:
        r = requests.get(POWER, params={"parameters": "PRECTOTCORR", "community": "AG",
                         "longitude": round(lon, 3), "latitude": round(lat, 3),
                         "format": "JSON"}, timeout=60).json()
        m = r["properties"]["parameter"]["PRECTOTCORR"]     # mm/day per month
        abbr = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
        total = 0.0
        for mon, key in enumerate(abbr, start=1):
            if key in m and m[key] > -900:
                total += m[key] * calendar.monthrange(2001, mon)[1]
        return round(total, 1)
    except Exception as e:
        print("  fail", round(lon, 2), round(lat, 2), e)
        return None


def idw(px, py, xs, ys, vs, power=2.0):
    d = np.sqrt((xs - px) ** 2 + (ys - py) ** 2)
    if np.any(d < 1e-9):
        return vs[np.argmin(d)]
    w = 1.0 / d ** power
    return float(np.sum(w * vs) / np.sum(w))


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    GEO.mkdir(parents=True, exist_ok=True)

    lons = np.linspace(AOI[0], AOI[2], NLON)
    lats = np.linspace(AOI[1], AOI[3], NLAT)
    rows = []
    for la in lats:
        for lo in lons:
            p = annual_precip(lo, la)
            if p is not None:
                rows.append({"lon": round(float(lo), 3), "lat": round(float(la), 3), "precip_mm": p})
                print(f"  {lo:6.2f},{la:5.2f}  {p:6.1f} mm/yr")
    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "rainshadow_grid.csv", index=False)

    xs, ys, vs = df["lon"].values, df["lat"].values, df["precip_mm"].values
    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    grid = np.empty((H, W), "float32")
    try:
        from scipy.interpolate import griddata
        gx, gy = np.meshgrid(np.linspace(AOI[0], AOI[2], W), np.linspace(AOI[3], AOI[1], H))
        grid = griddata((xs, ys), vs, (gx, gy), method="cubic")
        nan = np.isnan(grid)
        if nan.any():
            grid[nan] = griddata((xs, ys), vs, (gx[nan], gy[nan]), method="nearest")
        print("interpolated with scipy cubic")
    except Exception:
        for j in range(H):
            py = AOI[3] - j * RES
            for i in range(W):
                grid[j, i] = idw(AOI[0] + i * RES, py, xs, ys, vs)
        print("interpolated with IDW")

    transform = from_origin(AOI[0], AOI[3], RES, RES)
    with rasterio.open(GEO / "precip_rainshadow.tif", "w", driver="GTiff", height=H, width=W,
                       count=1, dtype="float32", crs="EPSG:4326", transform=transform,
                       nodata=np.nan, compress="deflate") as dst:
        dst.write(grid.astype("float32"), 1)
    print("wrote data/geo/precip_rainshadow.tif")

    north = df[df["lat"] > 31.2]["precip_mm"].mean()      # windward High Atlas
    south = df[df["lat"] < 30.6]["precip_mm"].mean()      # leeward Anti-Atlas / home
    print(f"\nwindward north (High Atlas)  {north:.0f} mm/yr")
    print(f"leeward south (Anti-Atlas)   {south:.0f} mm/yr")
    print(f"rain shadow: the south gets {100*(north-south)/north:.0f}% less rain than the north")


if __name__ == "__main__":
    main()

"""
measure_greenhouse.py
SETTLING THE OPEN QUESTION from panel 4.

Panel 4 found that land which was farmland in 2018 is markedly LESS green in 2026,
even after correcting for a record wet year. Two explanations survived, and NDVI
alone could not separate them:
  (a) the farms are failing  -> the ground reverts to BARE SOIL
  (b) open groves are being replaced by PLASTIC GREENHOUSES, which read dark to a
      vegetation index even though farming intensified

Those two look identical to NDVI, but they differ in the shortwave infrared and
the visible. So this script discriminates them spectrally.

Method (supervised by real reference areas, not by assumption):
  * Date-matched Sentinel-2 composites (blue, red, nir, swir16) for both years on
    one common grid.
  * Indices:
      NDVI = (NIR - Red)   / (NIR + Red)
      PMLI = (SWIR1 - Red) / (SWIR1 + Red)     plastic-mulched land index (Lu 2014)
      BRD  = (Blue - Red)  / (Blue + Red)      white plastic is bluer than ochre soil
      BRT  = mean(blue, red, nir) reflectance  brightness
  * Reference classes sampled from the landscape itself:
      PLASTIC ref = the Chtouka / Ait Amira greenhouse belt, a real greenhouse
                    district inside the study area (low-NDVI pixels there)
      SOIL ref    = bare desert that was bare in BOTH years
  * Every pixel that lost green is assigned to whichever reference it resembles,
    in standardised index space (nearest centroid).

Outputs: data/geo/souss_lostgreen_class.tif  (1 = plastic-like, 2 = soil-like)
         data/processed/greenhouse_test.csv
"""
from __future__ import annotations
import os
from pathlib import Path

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")

import numpy as np
import pandas as pd
import rasterio
import requests
from affine import Affine
from pyproj import Transformer
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds, transform as win_transform

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"
PROCESSED = ROOT / "data" / "processed"
STAC = "https://earth-search.aws.element84.com/v1/search"

AOI = (-9.60, 30.15, -8.55, 30.75)
RES = float(os.environ.get("GH_RES", "0.0006"))   # override for fast diagnostics
SCL_BAD = {3, 8, 9, 10}
YEARS = (2018, 2026)
BANDS = ("blue", "red", "nir", "swir16")
GREENHOUSE_REF = (-9.58, 30.15, -9.28, 30.34)   # Chtouka / Ait Amira greenhouse belt
LOST_GREEN = 0.15                                # NDVI drop that counts as losing green
FARM_2018 = 0.35                                 # was irrigated farmland in 2018


def scenes(year):
    r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-03-20T00:00:00Z/{year}-05-15T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 15}}, "limit": 60}, timeout=60).json()
    f = r.get("features", [])
    f.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return f


def band_on_grid(href, dst_t, W, H):
    """Read one band over the AOI and reproject onto the common lat/lon grid.
    Works for 10 m and 20 m bands since each computes its own window."""
    with rasterio.open(href) as src:
        tf = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
        xmin, ymin = tf.transform(AOI[0], AOI[1])
        xmax, ymax = tf.transform(AOI[2], AOI[3])
        win = from_bounds(xmin, ymin, xmax, ymax, src.transform)
        if win.width < 10 or win.height < 10:
            return None
        sc = max(1, int(win.width // (W * 1.2)))
        oh, ow = max(1, int(win.height // sc)), max(1, int(win.width // sc))
        arr = src.read(1, window=win, out_shape=(oh, ow)).astype("float32")
        src_t = win_transform(win, src.transform) * Affine.scale(win.width / ow, win.height / oh)
        crs = src.crs
    out = np.full((H, W), np.nan, "float32")
    reproject(arr, out, src_transform=src_t, src_crs=crs, dst_transform=dst_t,
              dst_crs="EPSG:4326", src_nodata=0, dst_nodata=np.nan,
              resampling=Resampling.bilinear)
    return out


def composite(year, dst_t, W, H, want=3):
    """Median composite of each band across the clearest scenes of that spring."""
    stacks = {b: [] for b in BANDS}
    used = 0
    for feat in scenes(year)[:10]:
        try:
            scl = band_on_grid(feat["assets"]["scl"]["href"], dst_t, W, H)
            if scl is None:
                continue
            good = ~np.isin(np.nan_to_num(scl, nan=-1).astype(int), list(SCL_BAD))
            vals = {}
            for b in BANDS:
                a = band_on_grid(feat["assets"][b]["href"], dst_t, W, H)
                if a is None:
                    raise ValueError("no window")
                a[~good] = np.nan
                vals[b] = a
        except Exception as e:
            print("   skip", feat["id"], str(e)[:50])
            continue
        cov = float(np.isfinite(vals["red"]).mean())
        print(f"   {feat['id']}  cloud={feat['properties']['eo:cloud_cover']:.1f}  valid={cov:.2f}")
        if cov > 0.15:
            for b in BANDS:
                stacks[b].append(vals[b])
            used += 1
        if used >= want:
            break
    if used == 0:
        return None
    return {b: np.nanmedian(np.dstack(stacks[b]), axis=2) for b in BANDS}


def indices(c):
    blue, red, nir, swir = (c[b] for b in ("blue", "red", "nir", "swir16"))

    def nd(a, b):
        return np.where((a + b) != 0, (a - b) / (a + b + 1e-6), np.nan)

    return {"ndvi": nd(nir, red), "pmli": nd(swir, red), "brd": nd(blue, red),
            "brt": (blue + red + nir) / 3.0 / 10000.0}


def main():
    GEO.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)
    print(f"common grid {W}x{H}")

    ix = {}
    for y in YEARS:
        print(f"\n{y}:")
        c = composite(y, dst_t, W, H)
        if c is None:
            print("  no usable scenes")
            return
        ix[y] = indices(c)

    y0, y1 = YEARS
    a0, a1 = ix[y0], ix[y1]
    both = (np.isfinite(a0["ndvi"]) & np.isfinite(a1["ndvi"]) & np.isfinite(a1["pmli"])
            & np.isfinite(a1["brd"]) & np.isfinite(a1["brt"]))

    lost = both & (a0["ndvi"] >= FARM_2018) & ((a0["ndvi"] - a1["ndvi"]) >= LOST_GREEN)

    lons = AOI[0] + (np.arange(W) + 0.5) * RES
    lats = AOI[3] - (np.arange(H) + 0.5) * RES
    LON, LAT = np.meshgrid(lons, lats)
    in_gh = ((LON >= GREENHOUSE_REF[0]) & (LON <= GREENHOUSE_REF[2])
             & (LAT >= GREENHOUSE_REF[1]) & (LAT <= GREENHOUSE_REF[3]))
    plastic_ref = both & in_gh & (a1["ndvi"] < 0.25)
    soil_ref = both & (a0["ndvi"] < 0.13) & (a1["ndvi"] < 0.18)

    feats = ("pmli", "brd", "brt")
    print(f"\nreference pixels: plastic={plastic_ref.sum():,}  soil={soil_ref.sum():,}  "
          f"lost-green={lost.sum():,}")
    minpx = int(os.environ.get("GH_MINPX", "500"))
    if plastic_ref.sum() < minpx or soil_ref.sum() < minpx or lost.sum() < minpx:
        print("  too few reference pixels - diagnosing:")
        print(f"    finite ndvi 2018 {np.isfinite(a0['ndvi']).sum():,} / 2026 {np.isfinite(a1['ndvi']).sum():,}")
        for f in ('pmli', 'brd', 'brt'):
            print(f"    finite {f} 2026  {np.isfinite(a1[f]).sum():,}")
        print(f"    both-valid       {both.sum():,}")
        print(f"    in greenhouse box {in_gh.sum():,}  (valid there {(both & in_gh).sum():,})")
        print(f"    farmland 2018    {(both & (a0['ndvi'] >= FARM_2018)).sum():,}")
        return

    print("\n2026 spectral signature of each class:")
    sig = {}
    for name, mask in (("plastic ref", plastic_ref), ("soil ref", soil_ref), ("lost green", lost)):
        sig[name] = [float(np.nanmedian(a1[f][mask])) for f in feats]
        print(f"  {name:12s} PMLI {sig[name][0]:+.3f}   BRD {sig[name][1]:+.3f}   "
              f"brightness {sig[name][2]:.3f}")

    ref_all = np.vstack([np.column_stack([a1[f][plastic_ref] for f in feats]),
                         np.column_stack([a1[f][soil_ref] for f in feats])])
    mu, sd = np.nanmean(ref_all, axis=0), np.nanstd(ref_all, axis=0) + 1e-9
    cp = (np.array(sig["plastic ref"]) - mu) / sd
    cs = (np.array(sig["soil ref"]) - mu) / sd
    # --- SEPARABILITY GATE -------------------------------------------------
    # Before classifying anything, check the classifier can even tell the two
    # REFERENCE classes apart. If it cannot separate its own training data, any
    # verdict on the unknown pixels is noise. This is the honesty check.
    def _assign(mask):
        Z = (np.column_stack([a1[f][mask] for f in feats]) - mu) / sd
        return np.linalg.norm(Z - cp, axis=1) < np.linalg.norm(Z - cs, axis=1)

    p_ok = float(_assign(plastic_ref).mean())
    s_ok = float(1.0 - _assign(soil_ref).mean())
    sep = 0.5 * (p_ok + s_ok)
    print("\nSEPARABILITY CHECK (can the two references be told apart?)")
    print(f"  plastic reference classified plastic : {100*p_ok:5.1f}%")
    print(f"  soil    reference classified soil    : {100*s_ok:5.1f}%")
    print(f"  balanced accuracy                    : {100*sep:5.1f}%   (50% = coin flip)")

    X = (np.column_stack([a1[f][lost] for f in feats]) - mu) / sd
    is_plastic = np.linalg.norm(X - cp, axis=1) < np.linalg.norm(X - cs, axis=1)

    px_km2 = (RES * 111.32) * (RES * 111.32 * np.cos(np.radians(30.45)))
    n = is_plastic.size
    pct_p = 100.0 * is_plastic.sum() / n
    if sep < 0.70:
        print("\n>>> INCONCLUSIVE: the plastic and soil signatures overlap too much for")
        print(">>> this index set to separate them reliably. The panel-4 question stays")
        print(">>> open; settling it needs finer reference data than NDVI/PMLI/BRD give.")
    print(f"\nOf the farmland that lost its green ({lost.sum() * px_km2:,.0f} km2):")
    print(f"  looks like PLASTIC GREENHOUSE : {pct_p:5.1f}%  ({is_plastic.sum() * px_km2:,.0f} km2)")
    print(f"  looks like BARE SOIL          : {100 - pct_p:5.1f}%  "
          f"({(n - is_plastic.sum()) * px_km2:,.0f} km2)")

    cls = np.zeros((H, W), "uint8")
    idx = np.where(lost)
    cls[idx[0], idx[1]] = np.where(is_plastic, 1, 2)
    with rasterio.open(GEO / "souss_lostgreen_class.tif", "w", driver="GTiff", height=H, width=W,
                       count=1, dtype="uint8", crs="EPSG:4326", transform=dst_t, nodata=0,
                       compress="deflate") as dst:
        dst.write(cls, 1)
    print("\nwrote data/geo/souss_lostgreen_class.tif  (1=plastic-like, 2=soil-like)")

    pd.DataFrame([{
        "lost_green_km2": round(float(lost.sum() * px_km2), 1),
        "plastic_like_pct": round(float(pct_p), 1),
        "soil_like_pct": round(float(100 - pct_p), 1),
        "plastic_like_km2": round(float(is_plastic.sum() * px_km2), 1),
        "soil_like_km2": round(float((n - is_plastic.sum()) * px_km2), 1),
        "separability_balanced_acc": round(float(sep), 3),
        "conclusive": bool(sep >= 0.70),
        "sig_plastic_pmli": round(sig["plastic ref"][0], 4),
        "sig_soil_pmli": round(sig["soil ref"][0], 4),
        "sig_lost_pmli": round(sig["lost green"][0], 4),
        "sig_plastic_brd": round(sig["plastic ref"][1], 4),
        "sig_soil_brd": round(sig["soil ref"][1], 4),
        "sig_lost_brd": round(sig["lost green"][1], 4),
    }]).to_csv(PROCESSED / "greenhouse_test.csv", index=False)
    print("wrote data/processed/greenhouse_test.csv")


if __name__ == "__main__":
    main()

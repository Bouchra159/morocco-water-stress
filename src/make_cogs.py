"""
make_cogs.py
Convert this repo's GeoTIFFs to Cloud Optimized GeoTIFFs (COG) - and validate them.

Why this matters. Every raster in this project is READ straight out of a COG on
S3: the Sentinel-2 scenes are Cloud Optimized GeoTIFFs, which is exactly why a
windowed read can pull one small area out of a 100 km scene without downloading
the whole thing. Until now the project consumed COGs but wrote plain GeoTIFFs.
This closes that loop, so the outputs can be served and read the same way.

What makes a GeoTIFF "cloud optimized":
  * internal TILING (512x512 blocks) so a reader can fetch one block by byte range
  * internal OVERVIEWS (pyramids) so a zoomed-out view reads a small pyramid level
  * a header laid out at the front of the file so one HTTP range request finds
    everything it needs

Following the validation-first practice from Ujaval Gandhi's "Agentic Coding for
Geospatial" course, this does not just convert - it re-opens every output and
CHECKS it, and reports any file that fails.

Usage:  python src/make_cogs.py            # convert data/geo/*.tif in place-safe way
        python src/make_cogs.py --check    # validate only, convert nothing

Outputs: data/geo/cog/<name>.tif  + data/processed/cog_report.csv
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd
import rasterio
from rasterio.enums import Resampling
from rasterio.shutil import copy as rio_copy

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / "data" / "geo"
COG_DIR = GEO / "cog"
PROCESSED = ROOT / "data" / "processed"

BLOCK = 512
OVERVIEW_LEVELS = [2, 4, 8, 16]
# categorical rasters must NOT be averaged when building pyramids
CATEGORICAL = {"landcover_souss.tif", "souss_lostgreen_class.tif", "souss_irrigated.tif"}


def is_cog(path: Path) -> tuple[bool, str]:
    """Re-open a file and check the things that actually make it cloud optimized."""
    try:
        with rasterio.open(path) as src:
            prof = src.profile
            tiled = bool(prof.get("tiled", False))
            bw, bh = prof.get("blockxsize"), prof.get("blockysize")
            n_ov = len(src.overviews(1))
            compressed = prof.get("compress") is not None
            small = src.width < 2 * BLOCK and src.height < 2 * BLOCK

            problems = []
            if not tiled:
                problems.append("not tiled")
            elif not (bw and bh and bw >= 256 and bh >= 256):
                problems.append(f"small blocks {bw}x{bh}")
            if n_ov == 0 and not small:
                problems.append("no overviews")
            if not compressed:
                problems.append("uncompressed")
            return (not problems), ("ok" if not problems else "; ".join(problems))
    except Exception as e:  # unreadable file is a failure, not a crash
        return False, f"unreadable: {e}"


def to_cog(src_path: Path, dst_path: Path) -> None:
    """Write a tiled, compressed, overview-bearing copy."""
    categorical = src_path.name in CATEGORICAL
    resampling = Resampling.nearest if categorical else Resampling.average

    with rasterio.open(src_path) as src:
        profile = src.profile.copy()
        profile.update(driver="GTiff", tiled=True, blockxsize=BLOCK, blockysize=BLOCK,
                       compress="deflate", predictor=1 if categorical else 3,
                       BIGTIFF="IF_SAFER")
        if profile.get("dtype") in ("uint8", "int8", "uint16", "int16", "int32"):
            profile["predictor"] = 2 if not categorical else 1

        tmp = dst_path.with_suffix(".tmp.tif")
        with rasterio.open(tmp, "w", **profile) as dst:
            for b in range(1, src.count + 1):
                dst.write(src.read(b), b)
            # only build pyramids that actually shrink the image
            levels = [f for f in OVERVIEW_LEVELS
                      if src.width // f >= 64 and src.height // f >= 64]
            if levels:
                dst.build_overviews(levels, resampling)
                dst.update_tags(ns="rio_overview", resampling=resampling.name)

    # COPY_SRC_OVERVIEWS moves the pyramids + header to the front of the file
    rio_copy(tmp, dst_path, driver="GTiff", copy_src_overviews=True,
             tiled=True, blockxsize=BLOCK, blockysize=BLOCK, compress="deflate",
             BIGTIFF="IF_SAFER")
    tmp.unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert and validate COGs.")
    ap.add_argument("--check", action="store_true", help="validate only, do not convert")
    args = ap.parse_args()

    PROCESSED.mkdir(parents=True, exist_ok=True)
    sources = sorted(p for p in GEO.glob("*.tif") if p.is_file())
    if not sources:
        print("no rasters found in data/geo")
        return

    if args.check:
        rows = []
        for p in sources:
            ok, note = is_cog(p)
            rows.append({"file": p.name, "cog": ok, "note": note})
            print(f"  {'PASS' if ok else 'FAIL'}  {p.name:32s} {note}")
        pd.DataFrame(rows).to_csv(PROCESSED / "cog_report.csv", index=False)
        n_ok = sum(r["cog"] for r in rows)
        print(f"\n{n_ok}/{len(rows)} already cloud optimized")
        return

    COG_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sources:
        dst = COG_DIR / p.name
        before_mb = p.stat().st_size / 1e6
        try:
            to_cog(p, dst)
        except Exception as e:
            print(f"  ERROR {p.name}: {e}")
            rows.append({"file": p.name, "cog": False, "note": f"convert failed: {e}",
                         "size_mb_before": round(before_mb, 2), "size_mb_after": None,
                         "overviews": 0})
            continue

        ok, note = is_cog(dst)                       # validate, never assume
        with rasterio.open(dst) as s:
            n_ov = len(s.overviews(1))
        after_mb = dst.stat().st_size / 1e6
        rows.append({"file": p.name, "cog": ok, "note": note,
                     "size_mb_before": round(before_mb, 2),
                     "size_mb_after": round(after_mb, 2), "overviews": n_ov})
        flag = "PASS" if ok else "FAIL"
        print(f"  {flag}  {p.name:32s} {before_mb:6.2f} -> {after_mb:6.2f} MB   "
              f"overviews={n_ov}   {note}")

    df = pd.DataFrame(rows)
    df.to_csv(PROCESSED / "cog_report.csv", index=False)
    n_ok = int(df["cog"].sum())
    print(f"\n{n_ok}/{len(df)} outputs validated as Cloud Optimized GeoTIFF")
    print(f"wrote data/geo/cog/  and data/processed/cog_report.csv")
    if n_ok != len(df):
        print("NOTE: files listed FAIL above did not meet the COG checks.")


if __name__ == "__main__":
    main()

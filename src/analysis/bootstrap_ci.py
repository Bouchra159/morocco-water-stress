"""
bootstrap_ci.py
How sure am I about the farmland decline?

The headline finding from the fourth Souss map is that land which was farmland in
2018 is 0.25 lower in NDVI by 2026, once the wet-year rainfall baseline is
subtracted. That is a single number. This puts an honest uncertainty range on it.

Why a BLOCK bootstrap and not the ordinary kind
    Satellite pixels next to each other are not independent observations. They
    belong to the same field, the same soil, the same irrigation scheme. If you
    resample individual pixels you are pretending to have hundreds of thousands
    of independent samples, and the confidence interval comes out absurdly tight
    - it would say plus or minus 0.001 and mean nothing.

    So this resamples SPATIAL BLOCKS (about 3 km across) with replacement. Each
    block carries its own internal correlation along with it, which is the
    standard way to bootstrap spatial data. The interval it produces is wider,
    and honest.

What is being estimated
    delta = (mean NDVI change on 2018 farmland) - (mean NDVI change on bare desert)
    The desert term is the rainfall baseline: land nobody irrigates, which greened
    on its own in the wet year of 2026.

Outputs: data/processed/bootstrap_ci.csv, figures/fig_bootstrap_ci.png
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "figures"

BLOCK = 50            # pixels per block side; at ~67 m that is about 3.3 km
N_BOOT = 2000
FARM_2018 = 0.35      # NDVI that counts as irrigated farmland in 2018
BARE_2018 = 0.13      # NDVI that counts as bare desert in 2018
SEED = 0


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)

    with rasterio.open(GEO / "souss_ndvi_2018.tif") as s:
        a0 = s.read(1)
    with rasterio.open(GEO / "souss_ndvi_2026.tif") as s:
        a1 = s.read(1)

    both = np.isfinite(a0) & np.isfinite(a1)
    change = a1 - a0
    farm = both & (a0 >= FARM_2018)
    bare = both & (a0 < BARE_2018)

    point_farm = float(np.nanmean(change[farm]))
    point_bare = float(np.nanmean(change[bare]))
    point_delta = point_farm - point_bare
    print(f"point estimate")
    print(f"  farmland 2018 mean NDVI change : {point_farm:+.4f}")
    print(f"  bare desert (rainfall baseline): {point_bare:+.4f}")
    print(f"  corrected difference           : {point_delta:+.4f}")

    # ---- build the block grid ------------------------------------------------
    H, W = change.shape
    nby, nbx = int(np.ceil(H / BLOCK)), int(np.ceil(W / BLOCK))
    blocks = []
    for by in range(nby):
        for bx in range(nbx):
            ys, ye = by * BLOCK, min((by + 1) * BLOCK, H)
            xs, xe = bx * BLOCK, min((bx + 1) * BLOCK, W)
            f = farm[ys:ye, xs:xe]
            b = bare[ys:ye, xs:xe]
            if f.sum() == 0 and b.sum() == 0:
                continue
            c = change[ys:ye, xs:xe]
            blocks.append((float(np.nansum(c[f])), int(f.sum()),
                           float(np.nansum(c[b])), int(b.sum())))
    if not blocks:
        print("no usable blocks")
        return

    arr = np.array(blocks)                       # columns: fsum, fn, bsum, bn
    n_blocks = len(arr)
    usable = int(((arr[:, 1] > 0) & (arr[:, 3] > 0)).sum())
    print(f"\n{n_blocks:,} spatial blocks of ~{BLOCK*67/1000:.1f} km "
          f"({usable:,} contain both farmland and desert)")

    # ---- block bootstrap -----------------------------------------------------
    rng = np.random.default_rng(SEED)
    deltas = np.empty(N_BOOT)
    for i in range(N_BOOT):
        pick = rng.integers(0, n_blocks, n_blocks)
        s = arr[pick]
        fn, bn = s[:, 1].sum(), s[:, 3].sum()
        if fn == 0 or bn == 0:
            deltas[i] = np.nan
            continue
        deltas[i] = (s[:, 0].sum() / fn) - (s[:, 2].sum() / bn)

    deltas = deltas[np.isfinite(deltas)]
    lo, hi = np.percentile(deltas, [2.5, 97.5])
    se = float(np.std(deltas, ddof=1))
    frac_neg = float((deltas < 0).mean())

    print(f"\nblock bootstrap, {len(deltas):,} resamples")
    print(f"  corrected difference : {point_delta:+.3f}")
    print(f"  95% CI               : {lo:+.3f} to {hi:+.3f}")
    print(f"  standard error       : {se:.3f}")
    print(f"  share of resamples below zero : {100*frac_neg:.1f}%")
    if hi < 0:
        print("\n  The whole interval sits below zero, so the direction of the")
        print("  finding holds: the old farmland lost green relative to the")
        print("  rainfall baseline. The size of the loss is uncertain within")
        print(f"  the range above.")
    else:
        print("\n  The interval crosses zero, so the direction of this finding")
        print("  is NOT established by the data.")

    pd.DataFrame([{
        "estimate": "farmland NDVI change minus rainfall baseline",
        "point": round(point_delta, 4),
        "ci95_low": round(float(lo), 4),
        "ci95_high": round(float(hi), 4),
        "std_error": round(se, 4),
        "n_blocks": n_blocks,
        "block_km": round(BLOCK * 67 / 1000, 1),
        "n_resamples": len(deltas),
        "farmland_change": round(point_farm, 4),
        "baseline_change": round(point_bare, 4),
    }]).to_csv(PROCESSED / "bootstrap_ci.csv", index=False)
    print("\nwrote data/processed/bootstrap_ci.csv")

    # ---- figure --------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.hist(deltas, bins=60, color="tab:brown", alpha=0.85)
    ax.axvline(point_delta, color="black", lw=2, label=f"estimate {point_delta:+.3f}")
    ax.axvline(lo, color="tab:red", ls="--", lw=1.4,
               label=f"95% CI  {lo:+.3f} to {hi:+.3f}")
    ax.axvline(hi, color="tab:red", ls="--", lw=1.4)
    ax.axvline(0, color="gray", lw=1)
    ax.set_xlabel("NDVI change on 2018 farmland, minus the bare-desert rainfall baseline")
    ax.set_ylabel("bootstrap resamples")
    ax.set_title("How sure is the farmland decline?\n"
                 f"block bootstrap, {BLOCK*67/1000:.1f} km blocks, {len(deltas):,} resamples")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "fig_bootstrap_ci.png", dpi=150)
    plt.close(fig)
    print("wrote figures/fig_bootstrap_ci.png")


if __name__ == "__main__":
    main()

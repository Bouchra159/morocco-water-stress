"""
classify_supervised.py
Supervised land-cover classification of the Souss plain, WITH a real accuracy
assessment - the standard remote-sensing workflow that an unsupervised K-means
map cannot give you.

Why this exists. `classify_landcover.py` clusters pixels with K-means and then
labels the clusters by eye. That is useful for exploration, but it can never tell
you how *right* it is. A supervised classifier can, because it is tested against
labels it never saw during training.

HONEST LIMIT, STATED UP FRONT
    There is no field survey for this area. Training labels here are derived from
    high-confidence spectral evidence plus locational priors (the Al Massira-style
    NDWI water test; the real Chtouka/Ait Amira greenhouse district; bare desert
    that stayed bare across years). They are photo-interpretation-grade, not
    ground-truth. So the accuracy below measures how well the model GENERALISES
    TO UNSEEN GROUND - not absolute agreement with reality.

    To make that generalisation claim meaningful, validation is SPATIALLY BLOCKED:
    the model trains on the western half of the plain and is tested on the eastern
    half, which it never sees. A random pixel split would leak neighbouring pixels
    between train and test and inflate accuracy dramatically; this does not.

Method
    Features : blue, green, red, nir, swir16, swir22 + NDVI, NDWI, NDBI, NDMI,
               PMLI, brightness  (12 features)
    Model    : RandomForestClassifier
    Report   : confusion matrix, overall accuracy, Cohen's kappa, and per-class
               precision / recall / F1

Outputs: data/geo/souss_landcover_supervised.tif   (classified raster)
         data/processed/classification_accuracy.csv (per-class metrics)
         data/processed/confusion_matrix.csv
         figures/fig_confusion_matrix.png
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
FIG = ROOT / "figures"
CACHE = GEO / "souss_stack_2026.tif"
STAC = "https://earth-search.aws.element84.com/v1/search"

AOI = (-9.60, 30.15, -8.55, 30.75)
RES = float(os.environ.get("CLS_RES", "0.0006"))     # ~60 m
SCL_BAD = {3, 8, 9, 10}
BANDS = ("blue", "green", "red", "nir", "swir16", "swir22")
GREENHOUSE_REF = (-9.58, 30.15, -9.28, 30.34)        # Chtouka / Ait Amira district

CLASSES = {
    1: ("Water", "#2a6f97"),
    2: ("Irrigated crops", "#1a7a3a"),
    3: ("Greenhouse / plastic", "#c9c2d6"),
    4: ("Natural shrub / argan", "#7ba05a"),
    5: ("Bare soil / desert", "#d9b98a"),
    6: ("Rock / mountain", "#9a8a7a"),
}


def scenes(year=2026):
    r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "bbox": list(AOI),
        "datetime": f"{year}-03-20T00:00:00Z/{year}-05-15T23:59:59Z",
        "query": {"eo:cloud_cover": {"lt": 15}}, "limit": 60}, timeout=60).json()
    f = r.get("features", [])
    f.sort(key=lambda x: x["properties"]["eo:cloud_cover"])
    return f


def band_on_grid(href, dst_t, W, H):
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


def build_stack(dst_t, W, H, want=3):
    """Median composite of the six bands; cached to disk so re-runs are instant."""
    if CACHE.exists():
        with rasterio.open(CACHE) as s:
            if s.width == W and s.height == H:
                print(f"using cached stack {CACHE.name}")
                return {b: s.read(i + 1) for i, b in enumerate(BANDS)}
    stacks = {b: [] for b in BANDS}
    used = 0
    for feat in scenes()[:10]:
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
    comp = {b: np.nanmedian(np.dstack(stacks[b]), axis=2) for b in BANDS}

    prof = dict(driver="GTiff", height=H, width=W, count=len(BANDS), dtype="float32",
                crs="EPSG:4326", transform=dst_t, nodata=np.nan, compress="deflate",
                tiled=True, blockxsize=512, blockysize=512)
    with rasterio.open(CACHE, "w", **prof) as dst:
        for i, b in enumerate(BANDS):
            dst.write(comp[b].astype("float32"), i + 1)
            dst.set_band_description(i + 1, b)
    print(f"cached band stack -> {CACHE.name}")
    return comp


def features(c):
    b, g, r = c["blue"], c["green"], c["red"]
    n, s1, s2 = c["nir"], c["swir16"], c["swir22"]

    def nd(x, y):
        return np.where((x + y) != 0, (x - y) / (x + y + 1e-6), np.nan)

    f = {"blue": b / 1e4, "green": g / 1e4, "red": r / 1e4, "nir": n / 1e4,
         "swir16": s1 / 1e4, "swir22": s2 / 1e4,
         "ndvi": nd(n, r), "ndwi": nd(g, n), "ndbi": nd(s1, n),
         "ndmi": nd(n, s1), "pmli": nd(s1, r), "brightness": (b + g + r + n) / 4e4}
    return f


def label_samples(f, LON, LAT, dem=None):
    """High-confidence training labels from spectral evidence + locational priors.
    Deliberately conservative: only pixels that are unambiguous get a label."""
    ndvi, ndwi, ndbi = f["ndvi"], f["ndwi"], f["pmli"]
    nd_wi, brt = f["ndwi"], f["brightness"]
    lab = np.zeros(ndvi.shape, "uint8")

    in_gh = ((LON >= GREENHOUSE_REF[0]) & (LON <= GREENHOUSE_REF[2])
             & (LAT >= GREENHOUSE_REF[1]) & (LAT <= GREENHOUSE_REF[3]))

    # 1 water - the NDWI test used throughout this repo
    lab[(nd_wi > 0.15) & (ndvi < 0.20)] = 1
    # 2 irrigated crops - dense, moist vegetation outside the greenhouse district
    lab[(ndvi > 0.55) & (f["ndmi"] > 0.15) & ~in_gh] = 2
    # 3 greenhouse / plastic - bright, non-green, inside the real greenhouse belt
    lab[in_gh & (ndvi < 0.22) & (brt > 0.22) & (f["pmli"] < 0.30)] = 3
    # 4 natural shrub / argan - moderate greenness, low moisture, not irrigated
    lab[(ndvi > 0.22) & (ndvi < 0.38) & (f["ndmi"] < 0.10) & ~in_gh] = 4
    # 5 bare soil / desert - no vegetation, bright, ochre
    lab[(ndvi < 0.13) & (brt > 0.20) & (nd_wi < 0.0)] = 5
    # 6 rock / mountain - dark, low vegetation, low moisture
    lab[(ndvi < 0.16) & (brt < 0.17) & (nd_wi < 0.0)] = 6

    finite = np.all(np.isfinite(np.dstack(list(f.values()))), axis=2)
    lab[~finite] = 0
    return lab


def main():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (accuracy_score, cohen_kappa_score, confusion_matrix,
                                 classification_report)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(exist_ok=True)
    W = int(round((AOI[2] - AOI[0]) / RES))
    H = int(round((AOI[3] - AOI[1]) / RES))
    dst_t = from_origin(AOI[0], AOI[3], RES, RES)
    print(f"grid {W}x{H} @ ~{RES*111320:.0f} m\n")

    comp = build_stack(dst_t, W, H)
    if comp is None:
        print("no usable scenes")
        return
    f = features(comp)

    lons = AOI[0] + (np.arange(W) + 0.5) * RES
    lats = AOI[3] - (np.arange(H) + 0.5) * RES
    LON, LAT = np.meshgrid(lons, lats)

    lab = label_samples(f, LON, LAT)
    names = [k for k in f]
    X_all = np.dstack([f[k] for k in names])

    print("training samples per class:")
    for c, (nm, _) in CLASSES.items():
        print(f"  {c} {nm:22s} {int((lab == c).sum()):>8,}")
    if min((lab == c).sum() for c in CLASSES) < 200:
        print("\nWARNING: at least one class has very few samples")

    # ---- SPATIALLY BLOCKED split: train west, test east (no pixel leakage) ----
    mid = AOI[0] + (AOI[2] - AOI[0]) / 2.0
    west, east = LON < mid, LON >= mid
    tr = (lab > 0) & west
    te = (lab > 0) & east
    print(f"\nspatially blocked split  train(west)={tr.sum():,}  test(east)={te.sum():,}")
    print(f"  split meridian: {mid:.3f} deg lon")

    # cap per class so one class cannot dominate
    rng = np.random.default_rng(0)
    def sample(mask, cap=20000):
        idx = []
        for c in CLASSES:
            w = np.flatnonzero((lab.ravel() == c) & mask.ravel())
            if w.size > cap:
                w = rng.choice(w, cap, replace=False)
            idx.append(w)
        return np.concatenate(idx)

    itr, ite = sample(tr), sample(te)
    Xf = X_all.reshape(-1, len(names))
    Xtr, ytr = Xf[itr], lab.ravel()[itr]
    Xte, yte = Xf[ite], lab.ravel()[ite]

    clf = RandomForestClassifier(n_estimators=300, min_samples_leaf=2, n_jobs=-1,
                                 random_state=0, class_weight="balanced_subsample")
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)

    oa = accuracy_score(yte, pred)
    kappa = cohen_kappa_score(yte, pred)
    present = sorted(set(yte) | set(pred))
    labels_present = [CLASSES[c][0] for c in present]

    print("\n" + "=" * 62)
    print("ACCURACY ASSESSMENT  (tested on the eastern half, never trained on)")
    print("=" * 62)
    print(f"  Overall accuracy : {oa*100:.1f}%")
    print(f"  Cohen's kappa    : {kappa:.3f}")
    print()
    print(classification_report(yte, pred, labels=present,
                                target_names=labels_present, digits=3, zero_division=0))

    cm = confusion_matrix(yte, pred, labels=present)
    cm_df = pd.DataFrame(cm, index=[f"true {n}" for n in labels_present],
                         columns=[f"pred {n}" for n in labels_present])
    cm_df.to_csv(PROCESSED / "confusion_matrix.csv")
    print("confusion matrix:\n", cm_df.to_string())

    rep = classification_report(yte, pred, labels=present, target_names=labels_present,
                                output_dict=True, zero_division=0)
    rows = [{"class": n, "precision": round(rep[n]["precision"], 3),
             "recall": round(rep[n]["recall"], 3), "f1": round(rep[n]["f1-score"], 3),
             "support": int(rep[n]["support"])} for n in labels_present]
    rows.append({"class": "OVERALL", "precision": None, "recall": None,
                 "f1": round(oa, 3), "support": int(len(yte))})
    rows.append({"class": "KAPPA", "precision": None, "recall": None,
                 "f1": round(kappa, 3), "support": None})
    pd.DataFrame(rows).to_csv(PROCESSED / "classification_accuracy.csv", index=False)

    imp = sorted(zip(names, clf.feature_importances_), key=lambda x: -x[1])
    print("\ntop features:", ", ".join(f"{n} {v:.3f}" for n, v in imp[:6]))

    # ---- classify the whole scene ----
    finite = np.all(np.isfinite(X_all), axis=2)
    out = np.zeros((H, W), "uint8")
    flat = Xf[finite.ravel()]
    if flat.size:
        out.ravel()[np.flatnonzero(finite.ravel())] = clf.predict(flat)
    prof = dict(driver="GTiff", height=H, width=W, count=1, dtype="uint8",
                crs="EPSG:4326", transform=dst_t, nodata=0, compress="deflate",
                tiled=True, blockxsize=512, blockysize=512)
    with rasterio.open(GEO / "souss_landcover_supervised.tif", "w", **prof) as dst:
        dst.write(out, 1)
    print("\nwrote data/geo/souss_landcover_supervised.tif")

    px_km2 = (RES * 111.32) * (RES * 111.32 * np.cos(np.radians(30.45)))
    print("\nclassified area:")
    for c, (nm, _) in CLASSES.items():
        print(f"  {nm:22s} {int((out == c).sum()) * px_km2:8,.0f} km2")

    # ---- confusion-matrix figure (plain matplotlib) ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cmn = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(7.6, 6.4))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(present)), labels_present, rotation=45, ha="right")
    ax.set_yticks(range(len(present)), labels_present)
    for i in range(len(present)):
        for j in range(len(present)):
            ax.text(j, i, f"{cmn[i, j]:.2f}", ha="center", va="center",
                    color="white" if cmn[i, j] > 0.5 else "black", fontsize=9)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(f"Confusion matrix (row-normalised)\nspatially blocked test  "
                 f"OA {oa*100:.1f}%   kappa {kappa:.3f}")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(FIG / "fig_confusion_matrix.png", dpi=150)
    plt.close(fig)
    print("wrote figures/fig_confusion_matrix.png")


if __name__ == "__main__":
    main()

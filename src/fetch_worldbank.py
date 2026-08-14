"""
fetch_worldbank.py
Download Morocco freshwater indicators from the open World Bank API.

No API key required. Re-runnable: overwrites the raw JSON and the tidy CSV
each time so the whole dataset is reproducible from scratch.

Indicators
----------
ER.H2O.INTR.PC  Renewable internal freshwater resources per capita (m3)
ER.H2O.INTR.K3  Renewable internal freshwater resources, total (billion m3)
ER.H2O.FWTL.ZS  Annual freshwater withdrawals, total (% of internal resources)
ER.H2O.FWAG.ZS  Annual freshwater withdrawals, agriculture (% of total withdrawal)
SP.POP.TOTL     Population, total
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

COUNTRY = "MAR"  # Morocco, ISO3
BASE = "https://api.worldbank.org/v2"

INDICATORS = {
    "ER.H2O.INTR.PC": "renewable_internal_pc_m3",
    "ER.H2O.INTR.K3": "renewable_internal_total_bcm",
    "ER.H2O.FWTL.ZS": "withdrawal_pct_internal",
    "ER.H2O.FWAG.ZS": "withdrawal_agriculture_pct",
    "SP.POP.TOTL": "population",
}


def fetch_indicator(code: str) -> list[dict]:
    """Pull the full time series for one indicator, following pagination."""
    rows: list[dict] = []
    page = 1
    while True:
        url = f"{BASE}/country/{COUNTRY}/indicator/{code}"
        params = {"format": "json", "per_page": 500, "page": page}

        # the API occasionally returns a transient 400/5xx; retry with backoff
        for attempt in range(4):
            resp = requests.get(url, params=params, timeout=30)
            if resp.ok:
                break
            time.sleep(1.5 * (attempt + 1))
        resp.raise_for_status()
        payload = resp.json()

        # World Bank returns [metadata, data]; data is null when empty
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            break

        meta, data = payload[0], payload[1]
        rows.extend(data)

        if page >= meta.get("pages", 1):
            break
        page += 1
        time.sleep(0.2)  # be polite to the API

    return rows


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)

    tidy_frames = []
    for code, friendly in INDICATORS.items():
        print(f"fetching {code} ({friendly}) ...", end=" ")
        rows = fetch_indicator(code)
        print(f"{len(rows)} rows")

        # keep the raw response for provenance
        (RAW / f"{code}.json").write_text(
            json.dumps(rows, indent=2), encoding="utf-8"
        )

        df = pd.DataFrame(
            {
                "year": [int(r["date"]) for r in rows],
                "value": [r["value"] for r in rows],
            }
        )
        df = df.dropna(subset=["value"]).sort_values("year")
        df["indicator"] = friendly
        tidy_frames.append(df)

    tidy = pd.concat(tidy_frames, ignore_index=True)
    wide = tidy.pivot(index="year", columns="indicator", values="value").sort_index()

    out_long = PROCESSED / "morocco_water_indicators_long.csv"
    out_wide = PROCESSED / "morocco_water_indicators.csv"
    tidy.to_csv(out_long, index=False)
    wide.to_csv(out_wide)

    print(f"\nwrote {out_long.relative_to(ROOT)}")
    print(f"wrote {out_wide.relative_to(ROOT)}")

    # quick sanity print
    pc = wide["renewable_internal_pc_m3"].dropna()
    print(
        f"\nper-capita renewable water: "
        f"{pc.iloc[0]:.0f} m3 ({pc.index[0]}) -> {pc.iloc[-1]:.0f} m3 ({pc.index[-1]})"
    )


if __name__ == "__main__":
    main()

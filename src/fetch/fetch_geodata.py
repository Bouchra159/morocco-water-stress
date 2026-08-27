"""
fetch_geodata.py
Download open administrative boundaries for Morocco (geoBoundaries, ADM1).

Public, openly licensed data only. This repo deliberately avoids any
basin-agency (ABHOER) research shapefiles so it stays cleanly publishable.
Re-runnable: skips the download if the file already exists.
"""

from __future__ import annotations

from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
GEO = ROOT / "data" / "geo"

# geoBoundaries gbOpen, Morocco, admin level 1 (regions) — CC BY 4.0
ADM1_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/MAR/ADM1/geoBoundaries-MAR-ADM1.geojson"
)
ADM0_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/"
    "releaseData/gbOpen/MAR/ADM0/geoBoundaries-MAR-ADM0.geojson"
)


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"exists, skipping {dest.name}")
        return
    print(f"downloading {dest.name} ...", end=" ")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    print(f"{len(resp.content) // 1024} KB")


def main() -> None:
    GEO.mkdir(parents=True, exist_ok=True)
    download(ADM0_URL, GEO / "morocco_adm0.geojson")
    download(ADM1_URL, GEO / "morocco_adm1.geojson")


if __name__ == "__main__":
    main()

"""
build_figures.py
The national charts, in plain standard matplotlib (no custom design):
  fig1  renewable freshwater per person, with the scarcity thresholds
  fig2  same water, more people (twin axis)
  fig3  share of withdrawals going to agriculture
  fig4  reported national reservoir fill rate

Reads data/processed/morocco_water_indicators.csv (run fetch_worldbank.py first).
"""
from __future__ import annotations
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
FIG = ROOT / "figures"


def main() -> None:
    FIG.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    df = pd.read_csv(PROCESSED / "morocco_water_indicators.csv", index_col="year")

    # fig1 — per-capita renewable water + thresholds
    pc = df["renewable_internal_pc_m3"].dropna()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(pc.index, pc.values, label="renewable water per person")
    ax.axhline(1000, color="orange", linestyle="--", linewidth=1, label="water-stress line (1,000 m³)")
    ax.axhline(500, color="red", linestyle="--", linewidth=1, label="absolute scarcity (500 m³)")
    ax.set_xlabel("Year"); ax.set_ylabel("m³ per person per year")
    ax.set_title("Renewable freshwater per person in Morocco, 1961–2022")
    ax.legend()
    fig.tight_layout(); fig.savefig(FIG / "fig1_percapita_decline.png", dpi=150); plt.close(fig)

    # fig2 — same water, more people
    total = df["renewable_internal_total_bcm"].dropna()
    pop = df["population"].dropna() / 1e6
    fig, ax1 = plt.subplots(figsize=(9, 5))
    l1, = ax1.plot(total.index, total.values, color="tab:blue", label="renewable water (billion m³)")
    ax1.set_xlabel("Year"); ax1.set_ylabel("Renewable water (billion m³)")
    ax1.set_ylim(0, total.max() * 1.5)
    ax2 = ax1.twinx()
    l2, = ax2.plot(pop.index, pop.values, color="tab:red", label="population (millions)")
    ax2.set_ylabel("Population (millions)"); ax2.grid(False)
    ax1.set_title("Same water, more people: Morocco 1961–2022")
    ax1.legend(handles=[l1, l2], loc="upper left")
    fig.tight_layout(); fig.savefig(FIG / "fig2_resource_vs_people.png", dpi=150); plt.close(fig)

    # fig3 — agriculture share of withdrawals
    ag = df["withdrawal_agriculture_pct"].dropna()
    yr = int(ag.index.max()); v = float(ag.loc[yr])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie([v, 100 - v], labels=[f"Agriculture ({v:.0f}%)", f"Other ({100 - v:.0f}%)"],
           colors=["tab:green", "lightgray"], startangle=90, wedgeprops={"edgecolor": "white"})
    ax.set_title(f"Share of freshwater withdrawals, Morocco ({yr})")
    fig.tight_layout(); fig.savefig(FIG / "fig3_agriculture_share.png", dpi=150); plt.close(fig)

    # fig4 — reported reservoir fill rate
    res = pd.read_csv(RAW / "reservoir_levels_reported.csv", comment="#", parse_dates=["date"])
    res["year"] = res["date"].dt.year
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(res["year"].astype(str), res["national_fill_pct"], color="tab:blue")
    ax.set_xlabel("Year"); ax.set_ylabel("Reservoir fill rate (%)")
    ax.set_ylim(0, 80)
    ax.set_title("Reported national reservoir fill rate, Morocco")
    fig.tight_layout(); fig.savefig(FIG / "fig4_reservoir_levels.png", dpi=150); plt.close(fig)

    print("wrote fig1–fig4 to", FIG.relative_to(ROOT))


if __name__ == "__main__":
    main()

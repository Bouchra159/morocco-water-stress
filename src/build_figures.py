"""
build_figures.py
Turn the processed indicators into the four story figures.

Run fetch_worldbank.py first so data/processed exists.
Figures are written to figures/ as PNG (150 dpi) for the README and StoryMap.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
FIG = ROOT / "figures"

# muted, print-friendly palette (works in light and dark backgrounds)
INK = "#1a1a1a"
CRISIS = "#b3261e"      # deep red for the crisis lines
WARN = "#e07a1f"        # amber
CALM = "#2a6f97"        # water blue
GREY = "#8a8a8a"

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "font.size": 11,
        "axes.edgecolor": "#cccccc",
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "grid.color": "#eeeeee",
        "grid.linewidth": 0.8,
        "axes.axisbelow": True,
    }
)


def _load() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "morocco_water_indicators.csv", index_col="year")


def fig_percapita_decline(df: pd.DataFrame) -> None:
    """Per-capita renewable water vs the two international scarcity thresholds."""
    pc = df["renewable_internal_pc_m3"].dropna()

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(pc.index, pc.values, color=CALM, lw=2.4, zorder=3)
    ax.fill_between(pc.index, pc.values, 0, color=CALM, alpha=0.06, zorder=1)

    # thresholds
    ax.axhline(1000, color=WARN, ls="--", lw=1.4)
    ax.axhline(500, color=CRISIS, ls="--", lw=1.4)
    ax.text(pc.index.min() + 1, 1035, "Water stress threshold (1,000 m³)",
            color=WARN, fontsize=9, va="bottom")
    ax.text(pc.index.min() + 1, 535, "Absolute scarcity threshold (500 m³)",
            color=CRISIS, fontsize=9, va="bottom")

    # endpoints
    for yr in (pc.index.min(), pc.index.max()):
        ax.scatter([yr], [pc.loc[yr]], color=CALM, zorder=4, s=28)
        ax.annotate(f"{pc.loc[yr]:.0f} m³\n{yr}",
                    (yr, pc.loc[yr]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=9, color=INK, fontweight="bold")

    ax.set_title("Morocco crossed the water-stress line around 2000",
                 fontsize=13, fontweight="bold", color=INK, loc="left")
    ax.set_ylabel("Renewable internal freshwater\nper capita (m³/year)")
    ax.set_xlabel("")
    ax.set_ylim(0, pc.max() * 1.12)
    ax.margins(x=0.02)
    fig.text(0.125, -0.02,
             "Source: World Bank Open Data, indicator ER.H2O.INTR.PC (renewable internal freshwater per capita).",
             fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_percapita_decline.png", bbox_inches="tight")
    plt.close(fig)


def fig_resource_vs_people(df: pd.DataFrame) -> None:
    """The water didn't shrink — the people multiplied. Twin-axis story figure."""
    total = df["renewable_internal_total_bcm"].dropna()
    pop = df["population"].dropna() / 1e6
    yrs = total.index.intersection(pop.index)

    fig, ax1 = plt.subplots(figsize=(9, 5.2))
    ax1.plot(yrs, total.loc[yrs], color=CALM, lw=2.4, label="Renewable water (fixed)")
    ax1.set_ylabel("Renewable internal freshwater\n(billion m³/year)", color=CALM)
    ax1.tick_params(axis="y", labelcolor=CALM)
    ax1.set_ylim(0, total.max() * 1.6)

    ax2 = ax1.twinx()
    ax2.plot(yrs, pop.loc[yrs], color=CRISIS, lw=2.4, label="Population")
    ax2.set_ylabel("Population (millions)", color=CRISIS)
    ax2.tick_params(axis="y", labelcolor=CRISIS)
    ax2.grid(False)

    # direct line labels so no legend decoding is needed
    last = yrs.max()
    ax1.annotate("Renewable water\n(fixed ≈ 29 bcm)",
                 (last, total.loc[last]), textcoords="offset points",
                 xytext=(-95, 14), color=CALM, fontsize=9, fontweight="bold")
    ax2.annotate("Population\n(×3 since 1961)",
                 (last, pop.loc[last]), textcoords="offset points",
                 xytext=(-92, -34), color=CRISIS, fontsize=9, fontweight="bold")

    ax1.set_title("Same water, three times the people",
                  fontsize=13, fontweight="bold", color=INK, loc="left")
    fig.text(0.125, -0.02,
             "Source: World Bank Open Data — ER.H2O.INTR.K3 (total renewable water) and SP.POP.TOTL (population).",
             fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig2_resource_vs_people.png", bbox_inches="tight")
    plt.close(fig)


def fig_agriculture_share(df: pd.DataFrame) -> None:
    """Where the water goes: agriculture dominates withdrawals."""
    ag = df["withdrawal_agriculture_pct"].dropna()
    latest_year = ag.index.max()
    ag_pct = ag.loc[latest_year]
    other_pct = 100 - ag_pct

    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    wedges, _ = ax.pie(
        [ag_pct, other_pct],
        colors=[WARN, "#dfe6ea"],
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
    )
    ax.text(0, 0.12, f"{ag_pct:.0f}%", ha="center", fontsize=30,
            fontweight="bold", color=WARN)
    ax.text(0, -0.22, "of all water\nwithdrawn goes\nto agriculture",
            ha="center", fontsize=11, color=INK)
    ax.set_title(f"Agriculture uses most of Morocco's water ({latest_year})",
                 fontsize=13, fontweight="bold", color=INK)
    fig.text(0.02, 0.02,
             "Source: World Bank Open Data, indicator ER.H2O.FWAG.ZS "
             "(agricultural share of total freshwater withdrawals).",
             fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_agriculture_share.png", bbox_inches="tight")
    plt.close(fig)


def fig_reservoir_levels() -> None:
    """Reported national dam fill rate — the visible face of the drought."""
    res = pd.read_csv(RAW / "reservoir_levels_reported.csv", comment="#",
                      parse_dates=["date"])
    res["year"] = res["date"].dt.year

    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = [CRISIS if v <= 33 else CALM for v in res["national_fill_pct"]]
    bars = ax.bar(res["year"].astype(str), res["national_fill_pct"],
                  color=colors, width=0.6)
    for bar, v in zip(bars, res["national_fill_pct"]):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.2, f"{v:.1f}%",
                ha="center", fontsize=10, fontweight="bold", color=INK)

    ax.set_ylim(0, 80)
    ax.set_ylabel("National reservoir fill rate (%)")
    ax.set_title("Morocco's dams are running dry (reported fill rates)",
                 fontsize=13, fontweight="bold", color=INK, loc="left")
    fig.text(0.125, -0.02,
             "Reported by Moroccan authorities / press (not World Bank). "
             "See data/raw/reservoir_levels_reported.csv for sourcing.",
             fontsize=8, color=GREY)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_reservoir_levels.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG.mkdir(exist_ok=True)
    df = _load()
    fig_percapita_decline(df)
    fig_resource_vs_people(df)
    fig_agriculture_share(df)
    fig_reservoir_levels()
    print("wrote 4 figures to", FIG.relative_to(ROOT))


if __name__ == "__main__":
    main()

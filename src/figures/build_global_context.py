"""
build_global_context.py
Al Massira next to the lakes everyone already knows about.

When I say a reservoir lost 91% of its surface, the number sounds like the Aral
Sea, and I think that comparison is worth making carefully rather than avoiding,
because it is the wrong comparison in an interesting way.

The Aral Sea and Lake Chad lost roughly the same share of their surface, but they
took most of a lifetime to do it, and they did not come back. Al Massira lost the
same share in seven years and then refilled past where it started. Those are two
different kinds of trouble. One is a place disappearing. The other is a place you
cannot plan around.

I am not claiming my reservoir is a disaster on the scale of the Aral Sea. It is
much smaller and it recovered. The point of the chart is the timescale.

Figures used, with sources:
  Aral Sea    68,478 km2 in 1960, down about 88% by 2018 (Wang et al. 2020,
              Journal of Arid Environments; UNEP).
  Lake Chad   about 25,000 km2 in 1963 to roughly 1,350 km2, about 90 to 95%.
              NASA notes it has risen and fallen since; it is not a clean line.
  Al Massira  98 km2 in 2017 to 9 km2 in 2024, then 125 km2 in 2026, measured in
              this repository from Sentinel-2.

Outputs: figures/fig_global_context.png
"""
from __future__ import annotations

import os
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _repo_root():
    try:
        return pathlib.Path(__file__).resolve().parents[2]
    except NameError:
        return pathlib.Path(os.environ.get("MOROCCO_REPO", os.getcwd()))


FIG = _repo_root() / "figures"

CASES = [
    # label, years taken, percent lost at the worst point, recovered?, note
    ("Aral Sea\n1960-2018", 58, 88, False, "68,478 km² to about 8,000"),
    ("Lake Chad\n1963-2020s", 60, 90, False, "about 25,000 km² to 1,350"),
    ("Al Massira\n2017-2024", 7, 91, True, "98 km² to 9, then 125 in 2026"),
]


def main() -> None:
    FIG.mkdir(exist_ok=True)
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6),
                                   gridspec_kw={"width_ratios": [1, 1.15]})

    labels = [c[0] for c in CASES]
    years = [c[1] for c in CASES]
    lost = [c[2] for c in CASES]
    colours = ["#8a8a8a", "#8a8a8a", "#b3261e"]

    # left: how much was lost
    ax1.barh(labels, lost, color=colours)
    for i, v in enumerate(lost):
        ax1.text(v - 3, i, f"{v}%", va="center", ha="right", color="white",
                 fontsize=11, fontweight="bold")
    ax1.set_xlim(0, 100)
    ax1.set_xlabel("Share of surface lost at the worst point (%)")
    ax1.set_title("They all lost about the same share")
    ax1.invert_yaxis()

    # right: how long it took
    ax2.barh(labels, years, color=colours)
    for i, v in enumerate(years):
        ax2.text(v + 1.2, i, f"{v} years", va="center", fontsize=10, color="#333")
    ax2.set_xlim(0, 70)
    ax2.set_xlabel("Years taken to lose it")
    ax2.set_title("But not in the same lifetime")
    ax2.invert_yaxis()

    ax2.text(9.6, 2.30, "and this one came back, to 125 km² in 2026",
             fontsize=9.5, color="#b3261e", va="center", style="italic")
    ax2.set_ylim(2.68, -0.55)

    fig.suptitle("A reservoir in Morocco, next to the lakes people already know about",
                 fontsize=13, y=0.99)
    fig.text(0.5, 0.015,
             "Aral Sea: Wang et al. 2020 / UNEP.  Lake Chad: NASA Earth Observatory, UNEP.  "
             "Al Massira: measured from Sentinel-2 in this repository.",
             ha="center", fontsize=7.5, color="#777")
    fig.tight_layout(rect=[0, 0.045, 1, 0.96])
    fig.savefig(FIG / "fig_global_context.png", dpi=150)
    plt.close(fig)
    print("wrote figures/fig_global_context.png")


if __name__ == "__main__":
    main()

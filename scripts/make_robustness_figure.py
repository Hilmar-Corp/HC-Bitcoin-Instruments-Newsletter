from pathlib import Path
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

TRACKING = (
    ROOT
    / "outputs/tables/publication_robustness_tracking_v1_1.csv"
)

PREMIUM = (
    ROOT
    / "outputs/tables/publication_robustness_premium_discount_v1_1.csv"
)

FIGURE = (
    ROOT
    / "publication/figures/06_measurement_robustness.png"
)

RESULTS = (
    ROOT
    / "publication/figures/robustness_figure_results_v1_1.json"
)

FIGURE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

NAVY = "#17384F"
BLUE = "#5D9FD3"
GREY = "#7D8991"
LIGHT_GREY = "#D7DEE3"
GRID = "#E6EAED"
BLACK = "#1B1B1B"

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "font.family": "DejaVu Sans",
    "font.size": 9.5,
    "axes.titlesize": 11.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.5,
    "text.color": BLACK,
})


tracking = pd.read_csv(TRACKING)
premium = pd.read_csv(PREMIUM)

tracking_order = [
    "xnas_simple_primary",
    "xnas_log_sensitivity",
    "utc00_simple_boundary_sensitivity",
    "utc00_log_boundary_sensitivity",
]

premium_order = [
    "full_sample",
    "remove_top_1pct_abs",
    "remove_top_5pct_abs",
]

if set(tracking["specification"]) != set(tracking_order):
    raise RuntimeError(
        "Unexpected tracking robustness specifications."
    )

if set(premium["specification"]) != set(premium_order):
    raise RuntimeError(
        "Unexpected premium/discount robustness specifications."
    )

t = (
    tracking
    .set_index("specification")
    .loc[tracking_order]
)

p = (
    premium
    .set_index("specification")
    .loc[premium_order]
)

tracking_labels = [
    "Clôture XNAS\nrendements simples",
    "Clôture XNAS\nlog-rendements",
    "00:00 UTC\nrendements simples",
    "00:00 UTC\nlog-rendements",
]

premium_labels = [
    "Échantillon complet",
    "Hors 1 % extrêmes",
    "Hors 5 % extrêmes",
]

fig, axes = plt.subplots(
    1,
    2,
    figsize=(12.4, 5.8),
    gridspec_kw={
        "width_ratios": [1.08, 1.0],
        "wspace": 0.34,
    },
)

ax = axes[0]

y = np.arange(len(t))

correlations = (
    t["correlation"]
    .to_numpy()
)

tracking_errors = (
    100
    * t["tracking_error_ann"]
    .to_numpy()
)

bars = ax.barh(
    y,
    correlations,
    height=0.56,
    color=[
        NAVY,
        BLUE,
        GREY,
        LIGHT_GREY,
    ],
)

ax.set_yticks(y)
ax.set_yticklabels(tracking_labels)
ax.invert_yaxis()

ax.set_xlim(0, 1.08)

ax.set_xlabel(
    "Corrélation quotidienne avec IBIT"
)

ax.set_title(
    "A. Sensibilité à la convention de mesure",
    loc="left",
)

ax.grid(
    True,
    axis="x",
    color=GRID,
    linewidth=0.7,
)

ax.grid(
    False,
    axis="y",
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

for bar, rho, te in zip(
    bars,
    correlations,
    tracking_errors,
):
    ax.text(
        min(rho + 0.022, 1.015),
        bar.get_y() + bar.get_height() / 2,
        (
            f"ρ = {rho:.3f}\n"
            f"TE = {te:.2f} %"
        ),
        va="center",
        ha="left",
        fontsize=8.3,
    )


ax = axes[1]

y = np.arange(len(p))

p05 = 100 * p["p05"].to_numpy()
p95 = 100 * p["p95"].to_numpy()
median = 100 * p["median"].to_numpy()
max_abs = 100 * p["max_abs"].to_numpy()

for i in range(len(p)):
    ax.hlines(
        y=i,
        xmin=p05[i],
        xmax=p95[i],
        color=NAVY,
        linewidth=2.5,
    )

    ax.scatter(
        median[i],
        i,
        s=45,
        color=BLUE,
        edgecolor="white",
        linewidth=0.8,
        zorder=3,
    )

    ax.text(
        p95[i] + 0.04,
        i,
        (
            f"méd. {median[i]:+.4f} %\n"
            f"max |x| {max_abs[i]:.4f} %"
        ),
        va="center",
        ha="left",
        fontsize=8.2,
    )

ax.axvline(
    0,
    color=GREY,
    linewidth=0.9,
)

ax.set_yticks(y)
ax.set_yticklabels(premium_labels)
ax.invert_yaxis()

ax.set_xlim(
    min(p05) - 0.15,
    max(p95) + 0.85,
)

ax.set_xlabel(
    "Prime / décote IBIT (%)"
)

ax.set_title(
    "B. Sensibilité aux observations extrêmes",
    loc="left",
)

ax.grid(
    True,
    axis="x",
    color=GRID,
    linewidth=0.7,
)

ax.grid(
    False,
    axis="y",
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)


fig.suptitle(
    "Robustesse aux conventions temporelles et aux queues de distribution",
    x=0.01,
    y=1.01,
    ha="left",
    fontsize=14,
    fontweight="bold",
)

fig.text(
    0.01,
    -0.015,
    (
        "La convention 00:00 UTC constitue un test de sensibilité volontairement "
        "non synchronisé avec la clôture d’IBIT ; elle n’est pas une estimation "
        "alternative du tracking. Panneau B : segments = 5e–95e percentiles. "
        "HilmarCorp Research."
    ),
    ha="left",
    va="top",
    fontsize=7.5,
    color="#65727A",
)

fig.savefig(
    FIGURE,
    dpi=240,
    bbox_inches="tight",
    pad_inches=0.18,
)

plt.close(fig)


results = {
    "status": "PASS",
    "figure": str(
        FIGURE.relative_to(ROOT)
    ),
    "xnas_simple": {
        "correlation": float(
            t.loc[
                "xnas_simple_primary",
                "correlation",
            ]
        ),
        "tracking_error_ann": float(
            t.loc[
                "xnas_simple_primary",
                "tracking_error_ann",
            ]
        ),
    },
    "xnas_log": {
        "correlation": float(
            t.loc[
                "xnas_log_sensitivity",
                "correlation",
            ]
        ),
        "tracking_error_ann": float(
            t.loc[
                "xnas_log_sensitivity",
                "tracking_error_ann",
            ]
        ),
    },
    "utc00_simple": {
        "correlation": float(
            t.loc[
                "utc00_simple_boundary_sensitivity",
                "correlation",
            ]
        ),
        "tracking_error_ann": float(
            t.loc[
                "utc00_simple_boundary_sensitivity",
                "tracking_error_ann",
            ]
        ),
    },
    "premium_discount": {
        name: {
            "median": float(
                p.loc[name, "median"]
            ),
            "p05": float(
                p.loc[name, "p05"]
            ),
            "p95": float(
                p.loc[name, "p95"]
            ),
            "max_abs": float(
                p.loc[name, "max_abs"]
            ),
        }
        for name in premium_order
    },
}

RESULTS.write_text(
    json.dumps(
        results,
        indent=2,
    )
    + "\n"
)

print(
    "SAVED",
    FIGURE.relative_to(ROOT),
)

print(
    "SAVED",
    RESULTS.relative_to(ROOT),
)

print("ROBUSTNESS FIGURE: PASS")

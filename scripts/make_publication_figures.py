from pathlib import Path
import json
import math

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SYNC = ROOT / "data/processed/panel_ibit_btc_SYNCHRONIZED.csv"
NAV = ROOT / "data/processed/panel_ibit_btc_nav_FINAL.csv"
CLAIMS = ROOT / "publication/claims_registry_v1_1.json"

OUT = ROOT / "publication/figures"
OUT.mkdir(parents=True, exist_ok=True)


# ============================================================
# VISUAL SYSTEM
# ============================================================

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
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.edgecolor": "#B8C0C5",
    "axes.linewidth": 0.8,
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "text.color": BLACK,
    "axes.labelcolor": BLACK,
    "legend.fontsize": 9,
})


def style_axis(ax):
    ax.grid(
        True,
        axis="both",
        color=GRID,
        linewidth=0.7,
        alpha=0.8,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color("#B8C0C5")
    ax.spines["bottom"].set_color("#B8C0C5")


def format_dates(ax):
    locator = mdates.AutoDateLocator(
        minticks=5,
        maxticks=8,
    )

    ax.xaxis.set_major_locator(locator)

    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(locator)
    )


def footer(fig, text):
    fig.text(
        0.01,
        0.012,
        text,
        ha="left",
        va="bottom",
        fontsize=7.5,
        color="#65727A",
    )


def save(fig, name):
    path = OUT / name

    fig.savefig(
        path,
        dpi=240,
        bbox_inches="tight",
        pad_inches=0.15,
    )

    plt.close(fig)

    print("SAVED", path.relative_to(ROOT))


# ============================================================
# LOAD + CONTRACT CHECKS
# ============================================================

sync = pd.read_csv(
    SYNC,
    parse_dates=["session_date"],
)

nav = pd.read_csv(
    NAV,
    parse_dates=["date"],
)

claims = json.loads(CLAIMS.read_text())


def claim(key):
    return float(
        claims["metrics"][key]["value"]
    )


assert len(sync) == 661
assert len(nav) == 661

assert sync["session_date"].is_unique
assert nav["date"].is_unique

assert sync["session_date"].is_monotonic_increasing
assert nav["date"].is_monotonic_increasing

assert sync["r_btc_sync"].notna().sum() == 660
assert sync["r_ibit"].notna().sum() == 660

assert sync["btc_close_at_xnas"].gt(0).all()
assert sync["ibit_close"].gt(0).all()

assert nav["btc"].gt(0).all()
assert nav["market"].gt(0).all()
assert nav["nav"].gt(0).all()

assert (
    sync["session_date"].reset_index(drop=True)
    ==
    nav["date"].reset_index(drop=True)
).all()

identity_max = (
    nav["identity_residual"]
    .dropna()
    .abs()
    .max()
)

assert identity_max < 1e-12


# ============================================================
# RECOMPUTE HEADLINE METRICS
# ============================================================

r = sync[
    ["r_btc_sync", "r_ibit", "tracking_diff"]
].dropna()

x = r["r_btc_sync"].to_numpy()
y = r["r_ibit"].to_numpy()

corr = float(np.corrcoef(x, y)[0, 1])

X = np.column_stack([
    np.ones(len(x)),
    x,
])

coef = np.linalg.lstsq(
    X,
    y,
    rcond=None,
)[0]

alpha = float(coef[0])
beta = float(coef[1])

pred = X @ coef

ss_res = float(
    np.sum((y - pred) ** 2)
)

ss_tot = float(
    np.sum((y - y.mean()) ** 2)
)

r2 = 1 - ss_res / ss_tot

td = (
    r["tracking_diff"]
    .to_numpy()
)

tracking_error_ann = (
    float(np.std(td, ddof=1))
    * math.sqrt(252)
)

premium = (
    nav["premium_discount"]
    .dropna()
)

premium_median = float(
    premium.median()
)

premium_p05 = float(
    premium.quantile(0.05)
)

premium_p95 = float(
    premium.quantile(0.95)
)

premium_max_abs = float(
    premium.abs().max()
)


# Claims registry must agree with recomputation.
assert abs(corr - claim("ibit.correlation")) < 1e-6
assert abs(beta - claim("ibit.beta")) < 1e-6
assert abs(r2 - claim("ibit.r2")) < 1e-6

assert (
    abs(
        tracking_error_ann
        - claim("ibit.tracking_error_ann")
    )
    < 1e-6
)

assert (
    abs(
        premium_median
        - claim("nav.premium_discount_median")
    )
    < 1e-6
)

assert (
    abs(
        premium_p05
        - claim("nav.premium_discount_p05")
    )
    < 1e-6
)

assert (
    abs(
        premium_p95
        - claim("nav.premium_discount_p95")
    )
    < 1e-6
)

assert (
    abs(
        premium_max_abs
        - claim("nav.premium_discount_max_abs")
    )
    < 1e-6
)


# ============================================================
# FIGURE 1
# BTC + IBIT INDEXED
# ============================================================

base = sync[
    [
        "session_date",
        "btc_close_at_xnas",
        "ibit_close",
    ]
].copy()

base["btc_index"] = (
    100
    * base["btc_close_at_xnas"]
    / base["btc_close_at_xnas"].iloc[0]
)

base["ibit_index"] = (
    100
    * base["ibit_close"]
    / base["ibit_close"].iloc[0]
)

fig, ax = plt.subplots(
    figsize=(10.8, 5.8)
)

ax.plot(
    base["session_date"],
    base["btc_index"],
    color=NAVY,
    linewidth=1.8,
    label="Bitcoin — Coinbase à la clôture XNAS",
)

ax.plot(
    base["session_date"],
    base["ibit_index"],
    color=BLUE,
    linewidth=1.5,
    label="IBIT — cours de clôture",
)

style_axis(ax)
format_dates(ax)

ax.set_title(
    "Bitcoin synchronisé et IBIT depuis le lancement d’IBIT",
    loc="left",
)

ax.set_ylabel(
    "Indice base 100 au 11 janvier 2024"
)

ax.legend(
    frameon=False,
    loc="upper left",
)

footer(
    fig,
    "Sources : Coinbase BTC-USD, IBIT. "
    "Bitcoin est observé exactement à la clôture effective XNAS. "
    "HilmarCorp Research.",
)

save(
    fig,
    "01_btc_ibit_indexed.png",
)


# ============================================================
# FIGURE 2
# DAILY RETURN REGRESSION
# ============================================================

fig, ax = plt.subplots(
    figsize=(7.6, 6.4)
)

ax.scatter(
    100 * x,
    100 * y,
    s=14,
    alpha=0.42,
    color=BLUE,
    edgecolors="none",
)

lo = min(
    float((100 * x).min()),
    float((100 * y).min()),
)

hi = max(
    float((100 * x).max()),
    float((100 * y).max()),
)

pad = 0.03 * (hi - lo)

line = np.linspace(
    lo - pad,
    hi + pad,
    200,
)

ax.plot(
    line,
    line,
    color=GREY,
    linewidth=1.1,
    linestyle="--",
    label="Ligne 45°",
)

reg_line = (
    100 * alpha
    + beta * line
)

ax.plot(
    line,
    reg_line,
    color=NAVY,
    linewidth=1.8,
    label="Régression OLS",
)

style_axis(ax)

ax.set_title(
    "Rendements quotidiens synchronisés : IBIT contre Bitcoin",
    loc="left",
)

ax.set_xlabel(
    "Rendement Bitcoin à la clôture XNAS (%)"
)

ax.set_ylabel(
    "Rendement IBIT (%)"
)

ax.text(
    0.035,
    0.965,
    (
        f"Corrélation = {corr:.6f}\n"
        f"β = {beta:.6f}\n"
        f"R² = {r2:.6f}\n"
        f"N = {len(r)}"
    ),
    transform=ax.transAxes,
    ha="left",
    va="top",
    fontsize=9,
    bbox={
        "facecolor": "white",
        "edgecolor": LIGHT_GREY,
        "boxstyle": "round,pad=0.45",
        "alpha": 0.94,
    },
)

ax.legend(
    frameon=False,
    loc="lower right",
)

footer(
    fig,
    "660 rendements synchronisés. "
    "Aucune interpolation et aucune observation future. "
    "HilmarCorp Research.",
)

save(
    fig,
    "02_ibit_btc_return_regression.png",
)


# ============================================================
# FIGURE 3
# DAILY TRACKING DIFFERENCE
# ============================================================

tracking = sync[
    [
        "session_date",
        "tracking_diff",
    ]
].dropna().copy()

tracking["tracking_bps"] = (
    10000
    * tracking["tracking_diff"]
)

tracking["rolling_20"] = (
    tracking["tracking_bps"]
    .rolling(
        20,
        min_periods=20,
    )
    .mean()
)

fig, ax = plt.subplots(
    figsize=(10.8, 5.8)
)

ax.plot(
    tracking["session_date"],
    tracking["tracking_bps"],
    color=BLUE,
    linewidth=0.75,
    alpha=0.62,
    label="Écart quotidien",
)

ax.plot(
    tracking["session_date"],
    tracking["rolling_20"],
    color=NAVY,
    linewidth=1.8,
    label="Moyenne mobile 20 séances",
)

ax.axhline(
    0,
    color=GREY,
    linewidth=0.9,
)

style_axis(ax)
format_dates(ax)

ax.set_title(
    "Écart quotidien entre le rendement d’IBIT et celui de Bitcoin",
    loc="left",
)

ax.set_ylabel(
    "IBIT − Bitcoin synchronisé (points de base)"
)

ax.legend(
    frameon=False,
    loc="upper right",
)

ax.text(
    0.015,
    0.035,
    (
        "Tracking error annualisée : "
        f"{100 * tracking_error_ann:.4f} %"
    ),
    transform=ax.transAxes,
    fontsize=9,
    color=BLACK,
)

footer(
    fig,
    "Écart calculé à partir des rendements simples quotidiens "
    "sur une frontière temporelle commune. HilmarCorp Research.",
)

save(
    fig,
    "03_ibit_tracking_difference.png",
)


# ============================================================
# FIGURE 4
# PREMIUM / DISCOUNT
# ============================================================

premium_df = nav[
    [
        "date",
        "premium_discount",
    ]
].copy()

premium_df["premium_pct"] = (
    100
    * premium_df["premium_discount"]
)

fig, ax = plt.subplots(
    figsize=(10.8, 5.8)
)

ax.plot(
    premium_df["date"],
    premium_df["premium_pct"],
    color=NAVY,
    linewidth=1.05,
)

ax.axhline(
    100 * premium_median,
    color=BLACK,
    linewidth=1.1,
    linestyle="--",
    label=(
        "Médiane "
        f"{100 * premium_median:.4f} %"
    ),
)

ax.axhline(
    100 * premium_p05,
    color=GREY,
    linewidth=0.9,
    linestyle=":",
)

ax.axhline(
    100 * premium_p95,
    color=GREY,
    linewidth=0.9,
    linestyle=":",
    label="5e–95e percentiles",
)

ax.axhline(
    0,
    color=LIGHT_GREY,
    linewidth=0.9,
)

style_axis(ax)
format_dates(ax)

ax.set_title(
    "Prime ou décote du prix de marché d’IBIT par rapport à sa NAV",
    loc="left",
)

ax.set_ylabel(
    "Prix de marché / NAV − 1 (%)"
)

ax.legend(
    frameon=False,
    loc="upper right",
)

footer(
    fig,
    "NAV issue du fichier officiel BlackRock/iShares. "
    "661 observations associées au panel certifié. "
    "HilmarCorp Research.",
)

save(
    fig,
    "04_ibit_premium_discount.png",
)


# ============================================================
# FIGURE 5
# EXACT LOG-GAP DECOMPOSITION
# ============================================================

decomp = nav[
    [
        "date",
        "gap_total",
        "gap_nav_vs_btc",
        "gap_market_vs_nav",
    ]
].copy()

for col in [
    "gap_total",
    "gap_nav_vs_btc",
    "gap_market_vs_nav",
]:
    decomp[col] = (
        decomp[col]
        .fillna(0.0)
    )

decomp["cum_total"] = (
    100
    * decomp["gap_total"].cumsum()
)

decomp["cum_nav"] = (
    100
    * decomp["gap_nav_vs_btc"].cumsum()
)

decomp["cum_market_nav"] = (
    100
    * decomp["gap_market_vs_nav"].cumsum()
)

decomp_residual = (
    decomp["cum_total"]
    - decomp["cum_nav"]
    - decomp["cum_market_nav"]
).abs().max()

assert decomp_residual < 1e-10

fig, ax = plt.subplots(
    figsize=(10.8, 5.8)
)

ax.plot(
    decomp["date"],
    decomp["cum_total"],
    color=BLACK,
    linewidth=2.0,
    label="Écart total : marché IBIT − Bitcoin",
)

ax.plot(
    decomp["date"],
    decomp["cum_nav"],
    color=NAVY,
    linewidth=1.5,
    label="NAV − Bitcoin",
)

ax.plot(
    decomp["date"],
    decomp["cum_market_nav"],
    color=BLUE,
    linewidth=1.5,
    label="Marché IBIT − NAV",
)

ax.axhline(
    0,
    color=GREY,
    linewidth=0.9,
)

style_axis(ax)
format_dates(ax)

ax.set_title(
    "Décomposition cumulative de l’écart entre IBIT et Bitcoin",
    loc="left",
)

ax.set_ylabel(
    "Écart cumulé en log-points (%)"
)

ax.legend(
    frameon=False,
    loc="best",
)

footer(
    fig,
    "Identité exacte en log-rendements : "
    "(marché − Bitcoin) = (NAV − Bitcoin) + (marché − NAV). "
    "HilmarCorp Research.",
)

save(
    fig,
    "05_ibit_tracking_decomposition.png",
)


# ============================================================
# BUILD REPORT
# ============================================================

report = {
    "status": "PASS",
    "observations_prices": int(len(sync)),
    "observations_returns": int(len(r)),
    "correlation": corr,
    "alpha_daily": alpha,
    "beta": beta,
    "r2": r2,
    "tracking_error_ann": tracking_error_ann,
    "premium_discount_median": premium_median,
    "premium_discount_p05": premium_p05,
    "premium_discount_p95": premium_p95,
    "premium_discount_max_abs": premium_max_abs,
    "identity_max_residual": float(identity_max),
    "cumulative_decomposition_max_residual": float(
        decomp_residual
    ),
    "figures": [
        "publication/figures/01_btc_ibit_indexed.png",
        "publication/figures/02_ibit_btc_return_regression.png",
        "publication/figures/03_ibit_tracking_difference.png",
        "publication/figures/04_ibit_premium_discount.png",
        "publication/figures/05_ibit_tracking_decomposition.png",
    ],
}

report_path = (
    OUT
    / "figure_build_results_v1_1.json"
)

report_path.write_text(
    json.dumps(
        report,
        indent=2,
    )
)

print()
print("=" * 72)
print("PUBLICATION FIGURES: PASS")
print("=" * 72)
print("Figures:", len(report["figures"]))
print("N prices:", len(sync))
print("N returns:", len(r))
print("Correlation:", f"{corr:.6f}")
print("Beta:", f"{beta:.6f}")
print("R2:", f"{r2:.6f}")
print(
    "Tracking error:",
    f"{100 * tracking_error_ann:.4f} %"
)
print(
    "Identity residual:",
    f"{identity_max:.3e}"
)
print(
    "Cumulative decomposition residual:",
    f"{decomp_residual:.3e}"
)

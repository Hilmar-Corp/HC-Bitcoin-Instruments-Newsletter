from pathlib import Path
import hashlib
import json
import math

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

SYNC = ROOT / "data/processed/panel_ibit_btc_SYNCHRONIZED.csv"
NAV = ROOT / "data/processed/panel_ibit_btc_nav_FINAL.csv"
RAW_CB = ROOT / "data/raw/coinbase_btcusd_1h.csv"
RAW_FREEZE = ROOT / "research/raw_freeze_v1_1.json"
CLAIMS = ROOT / "publication/claims_registry_v1_1.json"

PROC = ROOT / "data/processed"
TAB = ROOT / "outputs/tables"
REP = ROOT / "outputs/reports"

PROC.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)

ANN = 252


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def claim(registry, key):
    return float(
        registry["metrics"][key]["value"]
    )


def regression_metrics(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

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

    r2 = 1.0 - ss_res / ss_tot

    corr = float(
        np.corrcoef(x, y)[0, 1]
    )

    return {
        "correlation": corr,
        "alpha_daily": alpha,
        "beta": beta,
        "r2": r2,
    }


def simple_metrics(
    r_btc,
    r_ibit,
    specification,
    boundary,
):
    frame = pd.DataFrame({
        "btc": r_btc,
        "ibit": r_ibit,
    }).dropna()

    x = frame["btc"].to_numpy()
    y = frame["ibit"].to_numpy()

    reg = regression_metrics(x, y)

    diff = y - x

    te = float(
        np.std(
            diff,
            ddof=1,
        )
        * math.sqrt(ANN)
    )

    gross_ibit = float(
        np.prod(1.0 + y)
    )

    gross_btc = float(
        np.prod(1.0 + x)
    )

    n = len(frame)

    td_ann = float(
        (gross_ibit / gross_btc)
        ** (ANN / n)
        - 1.0
    )

    return {
        "specification": specification,
        "boundary": boundary,
        "return_definition": "simple",
        "n": int(n),
        **reg,
        "tracking_error_ann": te,
        "tracking_difference_ann_compounded": td_ann,
        "tracking_diff_mean": float(
            diff.mean()
        ),
        "tracking_diff_median": float(
            np.median(diff)
        ),
        "tracking_diff_p05": float(
            np.quantile(diff, 0.05)
        ),
        "tracking_diff_p95": float(
            np.quantile(diff, 0.95)
        ),
        "tracking_diff_max_abs": float(
            np.max(np.abs(diff))
        ),
    }


def log_metrics(
    p_btc,
    p_ibit,
    specification,
    boundary,
):
    p_btc = pd.Series(
        p_btc,
        dtype=float,
    )

    p_ibit = pd.Series(
        p_ibit,
        dtype=float,
    )

    log_btc = np.log(
        p_btc / p_btc.shift(1)
    )

    log_ibit = np.log(
        p_ibit / p_ibit.shift(1)
    )

    frame = pd.DataFrame({
        "btc": log_btc,
        "ibit": log_ibit,
    }).dropna()

    x = frame["btc"].to_numpy()
    y = frame["ibit"].to_numpy()

    reg = regression_metrics(x, y)

    diff = y - x

    te = float(
        np.std(
            diff,
            ddof=1,
        )
        * math.sqrt(ANN)
    )

    n = len(frame)

    td_ann = float(
        np.exp(
            diff.sum()
            * ANN
            / n
        )
        - 1.0
    )

    return {
        "specification": specification,
        "boundary": boundary,
        "return_definition": "log",
        "n": int(n),
        **reg,
        "tracking_error_ann": te,
        "tracking_difference_ann_compounded": td_ann,
        "tracking_diff_mean": float(
            diff.mean()
        ),
        "tracking_diff_median": float(
            np.median(diff)
        ),
        "tracking_diff_p05": float(
            np.quantile(diff, 0.05)
        ),
        "tracking_diff_p95": float(
            np.quantile(diff, 0.95)
        ),
        "tracking_diff_max_abs": float(
            np.max(np.abs(diff))
        ),
    }


def premium_stats(
    series,
    specification,
    removed_fraction,
):
    s = pd.Series(
        series,
        dtype=float,
    ).dropna()

    n_initial = len(s)

    if removed_fraction > 0:
        n_remove = int(
            math.ceil(
                removed_fraction
                * n_initial
            )
        )

        remove_index = (
            s.abs()
            .nlargest(n_remove)
            .index
        )

        s = s.drop(
            index=remove_index
        )
    else:
        n_remove = 0

    return {
        "specification": specification,
        "n": int(len(s)),
        "n_removed": int(n_remove),
        "removed_fraction_target":
            float(removed_fraction),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "mean_abs": float(s.abs().mean()),
        "p05": float(s.quantile(0.05)),
        "p95": float(s.quantile(0.95)),
        "max_abs": float(s.abs().max()),
    }


print("=" * 72)
print("HILMARCORP — PUBLICATION ROBUSTNESS V1.1")
print("=" * 72)


# ------------------------------------------------------------
# LOAD CERTIFIED INPUTS
# ------------------------------------------------------------

for path in [
    SYNC,
    NAV,
    RAW_CB,
    RAW_FREEZE,
    CLAIMS,
]:
    if not path.exists():
        raise FileNotFoundError(path)

sync = pd.read_csv(
    SYNC,
    parse_dates=["session_date"],
)

nav = pd.read_csv(
    NAV,
    parse_dates=["date"],
)

claims = json.loads(
    CLAIMS.read_text()
)

raw_freeze = json.loads(
    RAW_FREEZE.read_text()
)

assert len(sync) == 661
assert len(nav) == 661

assert sync["session_date"].is_unique
assert nav["date"].is_unique

assert (
    sync["session_date"]
    .reset_index(drop=True)
    ==
    nav["date"]
    .reset_index(drop=True)
).all()


# ------------------------------------------------------------
# RAW PROVENANCE
# ------------------------------------------------------------

coinbase_source = next(
    x
    for x in raw_freeze["sources"]
    if x["id"] == "coinbase_btcusd_1h"
)

raw_actual_hash = sha256(
    RAW_CB
)

raw_expected_hash = (
    coinbase_source["sha256"]
)

if raw_actual_hash != raw_expected_hash:
    raise RuntimeError(
        "Coinbase raw file does not match "
        "raw_freeze_v1_1.json"
    )

print(
    "RAW COINBASE HASH: PASS",
    raw_actual_hash[:16],
)


# ------------------------------------------------------------
# LOAD RAW COINBASE HOURLY
# ------------------------------------------------------------

cb = pd.read_csv(
    RAW_CB
)

if "time" not in cb.columns:
    raise RuntimeError(
        "Expected Coinbase raw column 'time'. "
        f"Found: {list(cb.columns)}"
    )

cb["time"] = pd.to_datetime(
    cb["time"],
    utc=True,
)

cb["close"] = pd.to_numeric(
    cb["close"],
    errors="coerce",
)

cb = (
    cb.dropna(
        subset=["time", "close"]
    )
    .drop_duplicates("time")
    .sort_values("time")
    .set_index("time")
)

if not cb.index.is_unique:
    raise RuntimeError(
        "Coinbase hourly index not unique."
    )


# ------------------------------------------------------------
# ALTERNATIVE TEMPORAL CONVENTION
#
# For session date D, use the Coinbase hourly candle
# ending exactly at 00:00 UTC at the START of D.
#
# Example:
# D = 2024-01-11
# boundary = 2024-01-11 00:00 UTC
# candle start = 2024-01-10 23:00 UTC
#
# This convention is deliberately NOT synchronized with
# the XNAS close. It is a temporal-boundary sensitivity.
#
# It uses no future observation relative to the IBIT close.
# ------------------------------------------------------------

rob = sync[
    [
        "session_date",
        "btc_close_at_xnas",
        "ibit_close",
        "r_btc_sync",
        "r_ibit",
    ]
].copy()

midnight_utc = (
    pd.to_datetime(
        rob["session_date"]
    )
    .dt.tz_localize("UTC")
)

candle_start = (
    midnight_utc
    - pd.Timedelta(hours=1)
)

utc_prices = (
    cb["close"]
    .reindex(
        pd.DatetimeIndex(
            candle_start
        )
    )
)

rob["btc_utc00_same_date"] = (
    utc_prices.to_numpy()
)

rob["utc00_boundary"] = (
    midnight_utc.astype(str)
)

rob["utc00_candle_start"] = (
    candle_start.astype(str)
)

coverage = float(
    rob[
        "btc_utc00_same_date"
    ]
    .notna()
    .mean()
)

print(
    "UTC00 EXACT COVERAGE:",
    f"{coverage:.4%}",
)

if coverage != 1.0:
    missing = rob.loc[
        rob["btc_utc00_same_date"].isna(),
        "session_date",
    ]

    raise RuntimeError(
        "UTC00 sensitivity requires exact "
        "boundaries for every session. "
        f"Missing: {missing.tolist()}"
    )

rob["r_btc_utc00"] = (
    rob["btc_utc00_same_date"]
    .pct_change(
        fill_method=None
    )
)

rob["log_r_btc_xnas"] = np.log(
    rob["btc_close_at_xnas"]
    / rob["btc_close_at_xnas"].shift(1)
)

rob["log_r_btc_utc00"] = np.log(
    rob["btc_utc00_same_date"]
    / rob["btc_utc00_same_date"].shift(1)
)

rob["log_r_ibit"] = np.log(
    rob["ibit_close"]
    / rob["ibit_close"].shift(1)
)

rob_path = (
    PROC
    / "panel_ibit_btc_robustness_v1_1.csv"
)

rob.to_csv(
    rob_path,
    index=False,
)


# ------------------------------------------------------------
# TRACKING ROBUSTNESS
# ------------------------------------------------------------

tracking_rows = []

tracking_rows.append(
    simple_metrics(
        rob["r_btc_sync"],
        rob["r_ibit"],
        "xnas_simple_primary",
        "exact_xnas_close",
    )
)

tracking_rows.append(
    log_metrics(
        rob["btc_close_at_xnas"],
        rob["ibit_close"],
        "xnas_log_sensitivity",
        "exact_xnas_close",
    )
)

tracking_rows.append(
    simple_metrics(
        rob["r_btc_utc00"],
        rob["r_ibit"],
        "utc00_simple_boundary_sensitivity",
        "00:00_utc_start_of_session_date",
    )
)

tracking_rows.append(
    log_metrics(
        rob["btc_utc00_same_date"],
        rob["ibit_close"],
        "utc00_log_boundary_sensitivity",
        "00:00_utc_start_of_session_date",
    )
)

tracking = pd.DataFrame(
    tracking_rows
)

primary = tracking.loc[
    tracking["specification"]
    == "xnas_simple_primary"
].iloc[0]

checks = {
    "correlation":
        "ibit.correlation",

    "beta":
        "ibit.beta",

    "r2":
        "ibit.r2",

    "tracking_error_ann":
        "ibit.tracking_error_ann",

    "tracking_difference_ann_compounded":
        "ibit.tracking_difference_ann",
}

for column, key in checks.items():
    observed = float(
        primary[column]
    )

    expected = claim(
        claims,
        key,
    )

    if abs(observed - expected) > 2e-6:
        raise RuntimeError(
            f"Primary robustness recomputation "
            f"does not match claim {key}: "
            f"{observed} vs {expected}"
        )

tracking_path = (
    TAB
    / "publication_robustness_tracking_v1_1.csv"
)

tracking.to_csv(
    tracking_path,
    index=False,
)


# ------------------------------------------------------------
# PREMIUM / DISCOUNT TAIL ROBUSTNESS
# ------------------------------------------------------------

premium = nav[
    "premium_discount"
].dropna()

premium_rows = [
    premium_stats(
        premium,
        "full_sample",
        0.00,
    ),
    premium_stats(
        premium,
        "remove_top_1pct_abs",
        0.01,
    ),
    premium_stats(
        premium,
        "remove_top_5pct_abs",
        0.05,
    ),
]

premium_table = pd.DataFrame(
    premium_rows
)

full = premium_table.loc[
    premium_table["specification"]
    == "full_sample"
].iloc[0]

premium_checks = {
    "median":
        "nav.premium_discount_median",

    "p05":
        "nav.premium_discount_p05",

    "p95":
        "nav.premium_discount_p95",

    "max_abs":
        "nav.premium_discount_max_abs",
}

for column, key in premium_checks.items():
    observed = float(
        full[column]
    )

    expected = claim(
        claims,
        key,
    )

    if abs(observed - expected) > 2e-6:
        raise RuntimeError(
            f"Premium/discount recomputation "
            f"does not match claim {key}: "
            f"{observed} vs {expected}"
        )

premium_path = (
    TAB
    / "publication_robustness_premium_discount_v1_1.csv"
)

premium_table.to_csv(
    premium_path,
    index=False,
)


# ------------------------------------------------------------
# STRUCTURAL CONSISTENCY CHECKS
# ------------------------------------------------------------

xnas_simple = tracking.loc[
    tracking["specification"]
    == "xnas_simple_primary"
].iloc[0]

xnas_log = tracking.loc[
    tracking["specification"]
    == "xnas_log_sensitivity"
].iloc[0]

td_identity_gap = abs(
    float(
        xnas_simple[
            "tracking_difference_ann_compounded"
        ]
    )
    -
    float(
        xnas_log[
            "tracking_difference_ann_compounded"
        ]
    )
)

if td_identity_gap > 1e-12:
    raise RuntimeError(
        "Simple/log compounded tracking "
        "difference identity failed."
    )

max_abs_sequence = (
    premium_table[
        "max_abs"
    ]
    .to_numpy()
)

if not (
    max_abs_sequence[0]
    > max_abs_sequence[1]
    > max_abs_sequence[2]
):
    raise RuntimeError(
        "Tail trimming did not reduce "
        "premium/discount max absolute value."
    )


# ------------------------------------------------------------
# REPORT
# ------------------------------------------------------------

utc_simple = tracking.loc[
    tracking["specification"]
    == "utc00_simple_boundary_sensitivity"
].iloc[0]

report = {
    "protocol":
        "PUBLICATION_ROBUSTNESS_V1.1",

    "status":
        "PASS",

    "research_scope":
        "publication_sensitivity_only",

    "primary_research_freeze_modified":
        False,

    "raw_provider_added":
        False,

    "source_hashes": {
        "coinbase_raw_actual":
            raw_actual_hash,

        "coinbase_raw_expected":
            raw_expected_hash,

        "sync_panel":
            sha256(SYNC),

        "nav_panel":
            sha256(NAV),

        "claims_registry":
            sha256(CLAIMS),
    },

    "temporal_sensitivity": {
        "alternative_boundary":
            "00:00 UTC at start of same XNAS session date",

        "future_information_used":
            False,

        "exact_boundary_coverage":
            coverage,

        "purpose":
            (
                "Descriptive sensitivity to temporal "
                "convention; not an alternative "
                "publication-grade tracking estimate."
            ),
    },

    "primary": {
        "correlation":
            float(
                xnas_simple["correlation"]
            ),

        "beta":
            float(
                xnas_simple["beta"]
            ),

        "r2":
            float(
                xnas_simple["r2"]
            ),

        "tracking_error_ann":
            float(
                xnas_simple[
                    "tracking_error_ann"
                ]
            ),

        "tracking_difference_ann_compounded":
            float(
                xnas_simple[
                    "tracking_difference_ann_compounded"
                ]
            ),
    },

    "log_return_sensitivity": {
        "correlation":
            float(
                xnas_log["correlation"]
            ),

        "beta":
            float(
                xnas_log["beta"]
            ),

        "r2":
            float(
                xnas_log["r2"]
            ),

        "tracking_error_ann":
            float(
                xnas_log[
                    "tracking_error_ann"
                ]
            ),

        "tracking_difference_ann_compounded":
            float(
                xnas_log[
                    "tracking_difference_ann_compounded"
                ]
            ),

        "simple_log_td_identity_gap":
            float(
                td_identity_gap
            ),
    },

    "utc00_boundary_sensitivity": {
        "correlation":
            float(
                utc_simple["correlation"]
            ),

        "beta":
            float(
                utc_simple["beta"]
            ),

        "r2":
            float(
                utc_simple["r2"]
            ),

        "tracking_error_ann":
            float(
                utc_simple[
                    "tracking_error_ann"
                ]
            ),

        "tracking_difference_ann_compounded":
            float(
                utc_simple[
                    "tracking_difference_ann_compounded"
                ]
            ),
    },

    "premium_discount_tail_sensitivity":
        premium_table.to_dict(
            orient="records"
        ),

    "outputs": [
        str(
            rob_path.relative_to(ROOT)
        ),
        str(
            tracking_path.relative_to(ROOT)
        ),
        str(
            premium_path.relative_to(ROOT)
        ),
    ],
}

report_path = (
    REP
    / "PUBLICATION_ROBUSTNESS_RESULTS.json"
)

report_path.write_text(
    json.dumps(
        report,
        indent=2,
    )
)


# ------------------------------------------------------------
# PRINT HUMAN-READABLE RESULTS
# ------------------------------------------------------------

print()
print("=" * 72)
print("TRACKING ROBUSTNESS")
print("=" * 72)

for _, row in tracking.iterrows():
    print()
    print(row["specification"])
    print(
        "  N       :",
        int(row["n"]),
    )
    print(
        "  corr    :",
        f"{row['correlation']:.6f}",
    )
    print(
        "  beta    :",
        f"{row['beta']:.6f}",
    )
    print(
        "  R2      :",
        f"{row['r2']:.6f}",
    )
    print(
        "  TE ann  :",
        f"{100 * row['tracking_error_ann']:.4f} %",
    )
    print(
        "  TD ann  :",
        (
            f"{100 * row['tracking_difference_ann_compounded']:.4f} %"
        ),
    )

print()
print("=" * 72)
print("PREMIUM / DISCOUNT TAIL ROBUSTNESS")
print("=" * 72)

for _, row in premium_table.iterrows():
    print()
    print(row["specification"])
    print(
        "  N       :",
        int(row["n"]),
    )
    print(
        "  removed :",
        int(row["n_removed"]),
    )
    print(
        "  median  :",
        f"{100 * row['median']:.4f} %",
    )
    print(
        "  mean |x|:",
        f"{100 * row['mean_abs']:.4f} %",
    )
    print(
        "  P05     :",
        f"{100 * row['p05']:.4f} %",
    )
    print(
        "  P95     :",
        f"{100 * row['p95']:.4f} %",
    )
    print(
        "  max |x| :",
        f"{100 * row['max_abs']:.4f} %",
    )

print()
print("=" * 72)
print("PUBLICATION ROBUSTNESS: PASS")
print("=" * 72)
print(
    "Panel:",
    rob_path.relative_to(ROOT),
)
print(
    "Tracking table:",
    tracking_path.relative_to(ROOT),
)
print(
    "Premium table:",
    premium_path.relative_to(ROOT),
)
print(
    "Report:",
    report_path.relative_to(ROOT),
)

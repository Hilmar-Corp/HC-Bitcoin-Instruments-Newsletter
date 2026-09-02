from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ANN = 252

ROOT = Path(".")
RAW  = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
TAB  = ROOT / "outputs" / "tables"
REP  = ROOT / "outputs" / "reports"

for p in [RAW, PROC, TAB, REP]:
    p.mkdir(parents=True, exist_ok=True)

print("=" * 78)
print("HILMARCORP — IBIT NAV / MARKET / BTC FINAL DECOMPOSITION")
print("=" * 78)

# ============================================================
# 1. OFFICIAL BLACKROCK FUND DOWNLOAD
# ============================================================

URL = (
    "https://www.blackrock.com/varnish-api/"
    "blk-one01-product-data/product-data/api/v1/get-fund-document"
    "?appSubType=ISHARES"
    "&appType=PRODUCT_PAGE"
    "&component=fundDownload"
    "&locale=en_US"
    "&portfolioId=333011"
    "&targetSite=us-ishares"
    "&userType=individual"
)

xls_path = RAW / "ibit_blackrock_official_fund_download.xls"

if not xls_path.exists():
    print("\n[DOWNLOAD] BlackRock official IBIT Excel")

    r = requests.get(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        },
        timeout=60,
    )

    print("HTTP:", r.status_code)
    print("Content-Type:", r.headers.get("content-type"))
    print("Bytes:", len(r.content))

    if r.status_code != 200 or len(r.content) < 1000:
        raise RuntimeError(
            "BlackRock Data Download failed."
        )

    xls_path.write_bytes(r.content)

else:
    print("\n[CACHE] BlackRock Excel already present")


# ============================================================
# NORMALIZED BLACKROCK WORKBOOK
# ============================================================

xls_path = RAW / "ibit_blackrock_official_fund_download_normalized.xlsx"

# ============================================================
# 2. INSPECT WORKBOOK
# ============================================================

book = pd.ExcelFile(xls_path, engine="openpyxl")

print("\n[SHEETS]")
for s in book.sheet_names:
    print(" -", s)

audit_dir = TAB / "blackrock_excel_audit"
audit_dir.mkdir(exist_ok=True)


def norm(x):
    x = str(x).strip().lower()
    x = re.sub(r"\s+", " ", x)
    return x


def clean_number(x):
    if pd.isna(x):
        return np.nan

    s = str(x).strip()
    s = s.replace("$", "")
    s = s.replace(",", "")
    s = s.replace("%", "")

    try:
        return float(s)
    except Exception:
        return np.nan


def choose_header(raw):
    best = None

    for i in range(min(100, len(raw))):
        vals = [
            norm(v)
            for v in raw.iloc[i].tolist()
            if pd.notna(v)
        ]

        blob = " | ".join(vals)

        score = 0

        if any(
            x in blob
            for x in ["date", "as of"]
        ):
            score += 3

        if "nav" in blob:
            score += 5

        if any(
            x in blob
            for x in [
                "market price",
                "closing price",
                "close"
            ]
        ):
            score += 2

        if "premium" in blob or "discount" in blob:
            score += 2

        if best is None or score > best[0]:
            best = (score, i)

    return best


candidates = []

for sheet in book.sheet_names:

    raw = pd.read_excel(
        xls_path,
        sheet_name=sheet,
        header=None
    )

    safe_name = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        sheet
    )

    raw.to_csv(
        audit_dir / f"{safe_name}_raw.csv",
        index=False
    )

    score, header_row = choose_header(raw)

    print(
        f"[SHEET] {sheet}: "
        f"header candidate row={header_row}, score={score}"
    )

    if score < 5:
        continue

    df = pd.read_excel(
        xls_path,
        sheet_name=sheet,
        header=header_row
    )

    df.columns = [
        norm(c)
        for c in df.columns
    ]

    print("        columns:", list(df.columns))

    date_cols = [
        c for c in df.columns
        if (
            c == "date"
            or c == "as of"
            or "as of date" in c
            or c.startswith("date ")
        )
    ]

    if not date_cols:
        date_cols = [
            c for c in df.columns
            if "date" in c
        ]

    nav_cols = [
        c for c in df.columns
        if (
            c == "nav"
            or c.startswith("nav ")
            or "nav per share" in c
        )
        and "return" not in c
        and "change" not in c
    ]

    if not date_cols or not nav_cols:
        continue

    date_col = date_cols[0]
    nav_col = nav_cols[0]

    tmp = pd.DataFrame()

    tmp["date"] = pd.to_datetime(
        df[date_col],
        errors="coerce"
    )

    tmp["nav"] = df[nav_col].map(
        clean_number
    )

    market_cols = [
        c for c in df.columns
        if any(
            k in c
            for k in [
                "market price",
                "closing price"
            ]
        )
    ]

    premium_cols = [
        c for c in df.columns
        if (
            "premium" in c
            and "discount" in c
        )
    ]

    if market_cols:
        tmp["blackrock_market_price"] = (
            df[market_cols[0]]
            .map(clean_number)
        )

    if premium_cols:
        tmp["blackrock_premium_discount_raw"] = (
            df[premium_cols[0]]
            .map(clean_number)
        )

    tmp = tmp.dropna(
        subset=["date", "nav"]
    )

    tmp = tmp[
        tmp["nav"] > 0
    ].copy()

    candidates.append(
        (
            len(tmp),
            sheet,
            tmp
        )
    )


# ============================================================
# 3. REQUIRE ACTUAL DAILY NAV HISTORY
# ============================================================

if not candidates:

    print("\n" + "=" * 78)
    print("NO DAILY NAV SERIES DETECTED IN BLACKROCK DOWNLOAD")
    print("=" * 78)
    print(
        "Workbook was archived and every sheet was exported "
        "to outputs/tables/blackrock_excel_audit/."
    )
    print(
        "No data will be fabricated or inferred."
    )

    raise RuntimeError(
        "BlackRock workbook does not expose a detectable daily NAV history."
    )


candidates.sort(
    key=lambda x: x[0],
    reverse=True
)

n_raw, chosen_sheet, nav = candidates[0]

print("\n[NAV]")
print("Chosen sheet :", chosen_sheet)
print("Rows detected:", n_raw)

nav["date"] = (
    pd.to_datetime(nav["date"])
    .dt.tz_localize(None)
    .dt.normalize()
)

nav = (
    nav
    .drop_duplicates("date")
    .sort_values("date")
)

nav.to_csv(
    RAW / "ibit_blackrock_nav_history.csv",
    index=False
)


# ============================================================
# 4. LOAD OUR ALREADY-CERTIFIED SYNCHRONIZED PANEL
# ============================================================

panel_path = (
    PROC /
    "panel_ibit_btc_SYNCHRONIZED.csv"
)

if not panel_path.exists():
    raise RuntimeError(
        "Missing panel_ibit_btc_SYNCHRONIZED.csv"
    )

panel = pd.read_csv(panel_path)

panel["date"] = pd.to_datetime(
    panel["session_date"]
).dt.normalize()

panel["btc"] = pd.to_numeric(
    panel["btc_close_at_xnas"],
    errors="coerce"
)

panel["market"] = pd.to_numeric(
    panel["ibit_close"],
    errors="coerce"
)

m = panel[
    ["date", "btc", "market"]
].merge(
    nav,
    on="date",
    how="inner"
)

m = (
    m
    .dropna(
        subset=[
            "btc",
            "market",
            "nav"
        ]
    )
    .sort_values("date")
    .reset_index(drop=True)
)

coverage = len(m) / len(panel)

print("\n[MERGE]")
print("Certified IBIT/BTC observations:", len(panel))
print("NAV matched observations        :", len(m))
print(f"NAV coverage                    : {coverage:.4%}")

if coverage < 0.90:
    raise RuntimeError(
        f"NAV coverage only {coverage:.2%}. "
        "Not sufficient for publication decomposition."
    )


# ============================================================
# 5. PRICE / NAV PREMIUM-DISCOUNT
# ============================================================

m["premium_discount"] = (
    m["market"] / m["nav"] - 1
)

pd_stats = {
    "n": int(
        m["premium_discount"]
        .notna()
        .sum()
    ),
    "mean": float(
        m["premium_discount"].mean()
    ),
    "median": float(
        m["premium_discount"].median()
    ),
    "p05": float(
        m["premium_discount"].quantile(.05)
    ),
    "p95": float(
        m["premium_discount"].quantile(.95)
    ),
    "min": float(
        m["premium_discount"].min()
    ),
    "max": float(
        m["premium_discount"].max()
    ),
    "max_abs": float(
        m["premium_discount"].abs().max()
    ),
    "share_premium": float(
        (m["premium_discount"] > 0).mean()
    ),
    "share_discount": float(
        (m["premium_discount"] < 0).mean()
    ),
}


# ============================================================
# 6. EXACT LOG-RETURN DECOMPOSITION
#
# market - BTC
# =
# (NAV - BTC)
# +
# (market - NAV)
#
# exact in log-return space
# ============================================================

for c in [
    "btc",
    "nav",
    "market"
]:
    m[f"log_{c}"] = np.log(
        m[c] / m[c].shift(1)
    )

m["gap_total"] = (
    m["log_market"]
    -
    m["log_btc"]
)

m["gap_nav_vs_btc"] = (
    m["log_nav"]
    -
    m["log_btc"]
)

m["gap_market_vs_nav"] = (
    m["log_market"]
    -
    m["log_nav"]
)

m["identity_residual"] = (
    m["gap_total"]
    -
    m["gap_nav_vs_btc"]
    -
    m["gap_market_vs_nav"]
)

valid = m.dropna(
    subset=[
        "gap_total",
        "gap_nav_vs_btc",
        "gap_market_vs_nav"
    ]
).copy()

identity_max = float(
    valid["identity_residual"]
    .abs()
    .max()
)


def component_stats(x):
    x = x.dropna()

    mean_log_ann = (
        float(x.mean() * ANN)
    )

    return {
        "n": int(len(x)),
        "mean_daily_log_gap":
            float(x.mean()),
        "median_daily_log_gap":
            float(x.median()),
        "tracking_error_ann":
            float(
                x.std(ddof=1)
                * np.sqrt(ANN)
            ),
        "annualized_log_drift":
            mean_log_ann,
        "annualized_compounded_drift":
            float(
                np.exp(mean_log_ann) - 1
            ),
        "p05":
            float(x.quantile(.05)),
        "p95":
            float(x.quantile(.95)),
        "max_abs":
            float(x.abs().max()),
    }


components = {
    "TOTAL_market_vs_BTC":
        component_stats(
            valid["gap_total"]
        ),

    "NAV_vs_BTC":
        component_stats(
            valid["gap_nav_vs_btc"]
        ),

    "MARKET_vs_NAV":
        component_stats(
            valid["gap_market_vs_nav"]
        ),
}


# ============================================================
# 7. OPTIONAL CROSS-CHECK AGAINST BLACKROCK P/D COLUMN
# ============================================================

pd_crosscheck = None

if (
    "blackrock_premium_discount_raw"
    in m.columns
):

    z = m.dropna(
        subset=[
            "premium_discount",
            "blackrock_premium_discount_raw"
        ]
    ).copy()

    if len(z) > 20:

        official = (
            z["blackrock_premium_discount_raw"]
            .astype(float)
        )

        calc = z["premium_discount"]

        # Determine whether official series is expressed
        # as decimal or percentage points.
        rmse_decimal = float(
            np.sqrt(
                np.mean(
                    (
                        official
                        - calc
                    ) ** 2
                )
            )
        )

        rmse_percent = float(
            np.sqrt(
                np.mean(
                    (
                        official / 100
                        - calc
                    ) ** 2
                )
            )
        )

        if rmse_percent < rmse_decimal:
            normalized = official / 100
            scale = "percentage_points_divided_by_100"
        else:
            normalized = official
            scale = "decimal"

        pd_crosscheck = {
            "n": int(len(z)),
            "detected_scale": scale,
            "rmse": float(
                np.sqrt(
                    np.mean(
                        (
                            normalized
                            - calc
                        ) ** 2
                    )
                )
            ),
            "max_abs_difference":
                float(
                    (
                        normalized
                        - calc
                    )
                    .abs()
                    .max()
                )
        }


# ============================================================
# 8. FINAL CERTIFICATION
# ============================================================

checks = {
    "NAV_coverage_ge_90pct":
        coverage >= .90,

    "NAV_positive":
        bool((m["nav"] > 0).all()),

    "market_positive":
        bool((m["market"] > 0).all()),

    "BTC_positive":
        bool((m["btc"] > 0).all()),

    "log_decomposition_identity":
        identity_max < 1e-12,

    "return_observations_ge_500":
        len(valid) >= 500,
}

final_pass = all(
    checks.values()
)

result = {
    "experiment":
        "IBIT NAV / market / BTC decomposition",

    "data": {
        "blackrock_source":
            "Official iShares IBIT Data Download",
        "chosen_sheet":
            chosen_sheet,
        "nav_rows_detected":
            int(n_raw),
        "merged_rows":
            int(len(m)),
        "coverage":
            float(coverage),
    },

    "premium_discount":
        pd_stats,

    "tracking_decomposition":
        components,

    "blackrock_premium_discount_crosscheck":
        pd_crosscheck,

    "identity_max_abs_residual":
        identity_max,

    "checks":
        checks,

    "publication_ready":
        final_pass,
}

(
    REP /
    "IBIT_NAV_FINAL_RESULTS.json"
).write_text(
    json.dumps(
        result,
        indent=2
    )
)

m.to_csv(
    PROC /
    "panel_ibit_btc_nav_FINAL.csv",
    index=False
)

pd.DataFrame([
    [
        "NAV coverage",
        coverage
    ],
    [
        "Premium/discount median",
        pd_stats["median"]
    ],
    [
        "Premium/discount p05",
        pd_stats["p05"]
    ],
    [
        "Premium/discount p95",
        pd_stats["p95"]
    ],
    [
        "Premium/discount max abs",
        pd_stats["max_abs"]
    ],
    [
        "Total TE market vs BTC",
        components[
            "TOTAL_market_vs_BTC"
        ]["tracking_error_ann"]
    ],
    [
        "TE NAV vs BTC",
        components[
            "NAV_vs_BTC"
        ]["tracking_error_ann"]
    ],
    [
        "TE market vs NAV",
        components[
            "MARKET_vs_NAV"
        ]["tracking_error_ann"]
    ],
], columns=[
    "metric",
    "value"
]).to_csv(
    TAB /
    "ibit_nav_headline_metrics.csv",
    index=False
)


# ============================================================
# 9. TERMINAL OUTPUT
# ============================================================

print("\n" + "=" * 78)
print("PREMIUM / DISCOUNT")
print("=" * 78)

print(
    "Median :",
    f"{pd_stats['median']:.4%}"
)

print(
    "P05    :",
    f"{pd_stats['p05']:.4%}"
)

print(
    "P95    :",
    f"{pd_stats['p95']:.4%}"
)

print(
    "Max abs:",
    f"{pd_stats['max_abs']:.4%}"
)

print("\n" + "=" * 78)
print("TRACKING DECOMPOSITION")
print("=" * 78)

for name, stats in components.items():

    print(
        f"\n{name}"
    )

    print(
        "  TE annualized :",
        f"{stats['tracking_error_ann']:.4%}"
    )

    print(
        "  Drift ann     :",
        f"{stats['annualized_compounded_drift']:.4%}"
    )

print("\nIDENTITY CHECK")
print(
    "max |residual| =",
    f"{identity_max:.3e}"
)

print("\nCHECKS")
for k, v in checks.items():
    print(
        f"{'PASS' if v else 'FAIL':4} — {k}"
    )

print("\n" + "=" * 78)
print(
    "FINAL NAV DECOMPOSITION:",
    "PASS" if final_pass else "FAIL"
)
print("=" * 78)

print("\nOUTPUTS")
print(
    "outputs/reports/IBIT_NAV_FINAL_RESULTS.json"
)
print(
    "outputs/tables/ibit_nav_headline_metrics.csv"
)
print(
    "data/processed/panel_ibit_btc_nav_FINAL.csv"
)


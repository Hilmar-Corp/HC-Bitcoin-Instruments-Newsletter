from pathlib import Path
import time
import json
import numpy as np
import pandas as pd
import requests
import yfinance as yf
import statsmodels.api as sm
import exchange_calendars as xcals

START = pd.Timestamp("2024-01-11", tz="UTC")
END   = pd.Timestamp("2026-09-01", tz="UTC")
ANN = 252

ROOT = Path(".")
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
REP = ROOT / "outputs" / "reports"
TAB = ROOT / "outputs" / "tables"

for p in [RAW, PROC, REP, TAB]:
    p.mkdir(parents=True, exist_ok=True)

print("=" * 72)
print("HILMARCORP — ETF/SPOT TEMPORAL SYNCHRONIZATION AUDIT")
print("=" * 72)

# ============================================================
# 1. NASDAQ/XNAS SESSION CALENDAR
# ============================================================

cal = xcals.get_calendar("XNAS")

schedule = cal.schedule.loc["2024-01-11":"2026-08-31"].copy()

def utc(x):
    x = pd.Timestamp(x)
    if x.tzinfo is None:
        return x.tz_localize("UTC")
    return x.tz_convert("UTC")

schedule["close_utc"] = [utc(x) for x in schedule["close"]]
schedule["open_utc"]  = [utc(x) for x in schedule["open"]]

schedule["session_date"] = [
    pd.Timestamp(x).date() for x in schedule.index
]

print(f"[XNAS] sessions: {len(schedule)}")
print(f"[XNAS] first: {schedule['session_date'].iloc[0]}")
print(f"[XNAS] last : {schedule['session_date'].iloc[-1]}")

# ============================================================
# 2. DOWNLOAD IBIT DAILY
# ============================================================

print("\n[DOWNLOAD] IBIT")

ibit = yf.download(
    "IBIT",
    start="2024-01-11",
    end="2026-09-01",
    auto_adjust=False,
    progress=False,
    actions=False,
    threads=False,
)

if isinstance(ibit.columns, pd.MultiIndex):
    if "IBIT" in ibit.columns.get_level_values(-1):
        ibit = ibit.xs("IBIT", axis=1, level=-1, drop_level=True)
    elif "IBIT" in ibit.columns.get_level_values(0):
        ibit = ibit.xs("IBIT", axis=1, level=0, drop_level=True)

ibit.columns = [str(c).lower().replace(" ", "_") for c in ibit.columns]

ibit = ibit.reset_index()

date_col = ibit.columns[0]
ibit["session_date"] = pd.to_datetime(ibit[date_col]).dt.date
ibit["ibit_close"] = pd.to_numeric(ibit["close"], errors="coerce")

ibit = ibit[["session_date", "ibit_close"]].dropna()

print(f"[IBIT] rows: {len(ibit)}")

# ============================================================
# 3. COINBASE BTC-USD HOURLY
#
# Coinbase candle:
# [time, low, high, open, close, volume]
#
# We fetch hourly bars.
# For an XNAS close at T, we use the CLOSE of the BTC candle
# beginning at T-1h, i.e. the final observed BTC price in the
# hourly interval ending exactly at T.
#
# No interpolation.
# No forward fill.
# No future price.
# ============================================================

print("\n[DOWNLOAD] Coinbase BTC-USD hourly")

URL = "https://api.exchange.coinbase.com/products/BTC-USD/candles"

fetch_start = START - pd.Timedelta(days=2)
fetch_end   = END + pd.Timedelta(days=1)

rows = []
cursor = fetch_start
chunk = pd.Timedelta(hours=250)

session = requests.Session()
session.headers.update({
    "User-Agent": "HilmarCorp-Research/1.0",
    "Accept": "application/json",
})

n_requests = 0

while cursor < fetch_end:
    stop = min(cursor + chunk, fetch_end)

    params = {
        "granularity": 3600,
        "start": cursor.isoformat(),
        "end": stop.isoformat(),
    }

    r = session.get(URL, params=params, timeout=30)
    r.raise_for_status()

    data = r.json()

    if not isinstance(data, list):
        raise RuntimeError(f"Unexpected Coinbase response: {data}")

    rows.extend(data)
    n_requests += 1

    if n_requests % 20 == 0:
        print(f"  requests={n_requests}, candles_raw={len(rows)}")

    cursor = stop
    time.sleep(0.12)

if not rows:
    raise RuntimeError("No Coinbase data downloaded")

cb = pd.DataFrame(
    rows,
    columns=["time", "low", "high", "open", "close", "volume"]
)

cb["time"] = pd.to_datetime(cb["time"], unit="s", utc=True)

for c in ["low", "high", "open", "close", "volume"]:
    cb[c] = pd.to_numeric(cb[c], errors="coerce")

cb = (
    cb.drop_duplicates("time")
      .sort_values("time")
      .set_index("time")
)

cb.to_csv(RAW / "coinbase_btcusd_1h.csv")

print(f"[COINBASE] unique hourly candles: {len(cb)}")
print(f"[COINBASE] start: {cb.index.min()}")
print(f"[COINBASE] end  : {cb.index.max()}")

# ============================================================
# 4. EXACT SESSION-BOUNDARY BTC PRICES
# ============================================================

matched = []

for _, row in schedule.iterrows():

    close_time = row["close_utc"]

    # hourly candle ending at market close
    candle_start = close_time - pd.Timedelta(hours=1)

    if candle_start not in cb.index:
        matched.append({
            "session_date": row["session_date"],
            "xnas_close_utc": close_time,
            "btc_candle_start": candle_start,
            "btc_close_at_xnas": np.nan,
            "matched": False,
        })
        continue

    btc_px = cb.loc[candle_start, "close"]

    # defensive case if duplicated lookup somehow produces Series
    if isinstance(btc_px, pd.Series):
        btc_px = btc_px.iloc[-1]

    matched.append({
        "session_date": row["session_date"],
        "xnas_close_utc": close_time,
        "btc_candle_start": candle_start,
        "btc_close_at_xnas": float(btc_px),
        "matched": True,
    })

btc_close = pd.DataFrame(matched)

coverage = btc_close["matched"].mean()

print("\n[SYNCHRONIZATION]")
print(f"XNAS closes with exact Coinbase hourly boundary: "
      f"{btc_close['matched'].sum()}/{len(btc_close)}")
print(f"Coverage: {coverage:.4%}")

btc_close.to_csv(
    TAB / "btc_prices_at_xnas_close_audit.csv",
    index=False
)

# Absolutely no interpolation.
if coverage < 0.995:
    raise RuntimeError(
        f"Boundary coverage too low ({coverage:.3%}). "
        "Experiment stopped rather than interpolating."
    )

# ============================================================
# 5. BUILD COMMON PANEL
# ============================================================

panel = (
    schedule[["session_date", "open_utc", "close_utc"]]
    .merge(btc_close, on="session_date", how="inner")
    .merge(ibit, on="session_date", how="inner")
)

panel = panel.dropna(
    subset=["btc_close_at_xnas", "ibit_close"]
).copy()

panel = panel.sort_values("session_date").reset_index(drop=True)

panel["r_btc_sync"] = panel["btc_close_at_xnas"].pct_change()
panel["r_ibit"] = panel["ibit_close"].pct_change()

panel["tracking_diff"] = (
    panel["r_ibit"] - panel["r_btc_sync"]
)

panel["abs_tracking_diff"] = panel["tracking_diff"].abs()

panel.to_csv(
    PROC / "panel_ibit_btc_SYNCHRONIZED.csv",
    index=False
)

# ============================================================
# 6. METRICS
# ============================================================

x = panel[["r_ibit", "r_btc_sync"]].dropna().copy()

corr = x["r_ibit"].corr(x["r_btc_sync"])

X = sm.add_constant(x["r_btc_sync"])

model = sm.OLS(
    x["r_ibit"],
    X
).fit(cov_type="HC1")

beta = float(model.params["r_btc_sync"])
alpha = float(model.params["const"])
r2 = float(model.rsquared)

diff = panel["tracking_diff"].dropna()

te = float(
    diff.std(ddof=1) * np.sqrt(ANN)
)

gross_ibit = np.prod(1 + panel["r_ibit"].dropna())
gross_btc  = np.prod(1 + panel["r_btc_sync"].dropna())

N = len(x)

td_ann = float(
    (gross_ibit / gross_btc) ** (ANN / N) - 1
)

stats = {
    "protocol": "ETF_SPOT_SYNC_V1.1",
    "status": "PASS" if coverage >= .995 else "FAIL",
    "sample_start": str(panel["session_date"].min()),
    "sample_end": str(panel["session_date"].max()),
    "price_observations": int(len(panel)),
    "return_observations": int(N),
    "boundary_coverage": float(coverage),
    "correlation": float(corr),
    "beta": beta,
    "alpha_daily": alpha,
    "alpha_annual_approx": alpha * ANN,
    "r2": r2,
    "tracking_error_annualized": te,
    "tracking_difference_annualized_compounded": td_ann,
    "tracking_diff_mean_daily": float(diff.mean()),
    "tracking_diff_median_daily": float(diff.median()),
    "tracking_diff_p05": float(diff.quantile(.05)),
    "tracking_diff_p95": float(diff.quantile(.95)),
    "tracking_diff_max_abs": float(diff.abs().max()),
}

with open(REP / "ETF_SYNC_RESULTS.json", "w") as f:
    json.dump(stats, f, indent=2)

summary = f"""
HILMARCORP — ETF/SPOT SYNCHRONIZED TEST
---------------------------------------

Sample:
{stats['sample_start']} -> {stats['sample_end']}

Boundary coverage:
{stats['boundary_coverage']:.4%}

N returns:
{stats['return_observations']}

Correlation IBIT / BTC synchronized:
{stats['correlation']:.6f}

Beta:
{stats['beta']:.6f}

R²:
{stats['r2']:.6f}

Alpha daily:
{stats['alpha_daily']:.8f}

Tracking error annualized:
{stats['tracking_error_annualized']:.4%}

Tracking difference annualized compounded:
{stats['tracking_difference_annualized_compounded']:.4%}

Daily tracking difference:
mean   = {stats['tracking_diff_mean_daily']:.6%}
median = {stats['tracking_diff_median_daily']:.6%}
p05    = {stats['tracking_diff_p05']:.6%}
p95    = {stats['tracking_diff_p95']:.6%}
maxabs = {stats['tracking_diff_max_abs']:.6%}

STATUS:
{stats['status']}

IMPORTANT:
The previous Yahoo daily BTC comparison is superseded.
Do not use the previous correlation, beta, R² or tracking error.
"""

print("\n" + "=" * 72)
print(summary)
print("=" * 72)

(REP / "ETF_SYNC_SUMMARY.txt").write_text(summary)

print("\nFILES")
print("-----")
print("data/raw/coinbase_btcusd_1h.csv")
print("data/processed/panel_ibit_btc_SYNCHRONIZED.csv")
print("outputs/tables/btc_prices_at_xnas_close_audit.csv")
print("outputs/reports/ETF_SYNC_RESULTS.json")
print("outputs/reports/ETF_SYNC_SUMMARY.txt")


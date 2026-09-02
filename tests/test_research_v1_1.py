from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

CONTRACT = json.loads(
    (ROOT / "research/contract_v1_1.json").read_text()
)

SYNC = ROOT / "data/processed/panel_ibit_btc_SYNCHRONIZED.csv"
NAV = ROOT / "data/processed/panel_ibit_btc_nav_FINAL.csv"
AUDIT = ROOT / "outputs/tables/btc_prices_at_xnas_close_audit.csv"
ETF_REPORT = ROOT / "outputs/reports/ETF_SYNC_RESULTS.json"
NAV_REPORT = ROOT / "outputs/reports/IBIT_NAV_FINAL_RESULTS.json"
FREEZE = ROOT / "research/freeze_v1_1.json"


def sha256(path):
    h = hashlib.sha256()

    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)

    return h.hexdigest()


def load_sync():
    d = pd.read_csv(SYNC)
    d["session_date"] = pd.to_datetime(d["session_date"])
    return d.sort_values("session_date").reset_index(drop=True)


def load_nav():
    d = pd.read_csv(NAV)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def ols(y, x):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    xm = x.mean()
    ym = y.mean()

    beta = np.sum((x-xm)*(y-ym)) / np.sum((x-xm)**2)
    alpha = ym - beta*xm

    fitted = alpha + beta*x
    r2 = 1 - np.sum((y-fitted)**2) / np.sum((y-ym)**2)

    return alpha, beta, r2


# ------------------------------------------------------------
# ARTIFACTS
# ------------------------------------------------------------

def test_required_artifacts_exist():
    for p in [SYNC, NAV, AUDIT, ETF_REPORT, NAV_REPORT]:
        assert p.exists(), f"Missing artifact: {p}"


# ------------------------------------------------------------
# SAMPLE / DATA INTEGRITY
# ------------------------------------------------------------

def test_sample_integrity():
    d = load_sync()

    assert len(d) == 661
    assert d["session_date"].nunique() == 661

    assert d["session_date"].min() == pd.Timestamp("2024-01-11")
    assert d["session_date"].max() == pd.Timestamp("2026-08-31")

    assert d["btc_close_at_xnas"].notna().all()
    assert d["ibit_close"].notna().all()

    assert (d["btc_close_at_xnas"] > 0).all()
    assert (d["ibit_close"] > 0).all()

    assert d["session_date"].is_monotonic_increasing


def test_nav_integrity():
    d = load_nav()

    assert len(d) == 661
    assert d["date"].nunique() == 661

    assert d["date"].min() == pd.Timestamp("2024-01-11")
    assert d["date"].max() == pd.Timestamp("2026-08-31")

    for c in ["btc", "market", "nav"]:
        assert d[c].notna().all()
        assert (d[c] > 0).all()


def test_identical_calendar():
    a = load_sync()
    b = load_nav()

    assert np.array_equal(
        a["session_date"].values,
        b["date"].values
    )


# ------------------------------------------------------------
# ETF METRICS — RECOMPUTED FROM RAW PANEL
# ------------------------------------------------------------

def test_ibit_metrics():
    d = load_sync()

    btc = d["btc_close_at_xnas"].pct_change().dropna()
    ibit = d["ibit_close"].pct_change().dropna()

    assert len(btc) == 660
    assert len(ibit) == 660

    x = btc.to_numpy()
    y = ibit.to_numpy()

    corr = np.corrcoef(x, y)[0,1]
    alpha, beta, r2 = ols(y, x)

    diff = y - x

    te = np.std(diff, ddof=1) * np.sqrt(252)

    td = (
        (np.prod(1+y) / np.prod(1+x))
        ** (252 / len(x))
        - 1
    )

    exp = CONTRACT["ibit"]["metrics"]

    assert corr == pytest.approx(exp["correlation"], abs=2e-6)
    assert beta == pytest.approx(exp["beta"], abs=2e-6)
    assert r2 == pytest.approx(exp["r2"], abs=2e-6)
    assert te == pytest.approx(
        exp["tracking_error_ann_simple_returns"],
        abs=1e-5
    )
    assert td == pytest.approx(
        exp["tracking_difference_ann"],
        abs=1e-5
    )


# ------------------------------------------------------------
# NAV / MARKET / BTC EXACT DECOMPOSITION
# ------------------------------------------------------------

def test_log_return_identity():
    d = load_nav()

    rb = np.log(d["btc"] / d["btc"].shift(1))
    rn = np.log(d["nav"] / d["nav"].shift(1))
    rm = np.log(d["market"] / d["market"].shift(1))

    total = rm - rb
    nav_btc = rn - rb
    market_nav = rm - rn

    residual = total - nav_btc - market_nav

    assert residual.dropna().abs().max() < 1e-12


def test_premium_discount():
    d = load_nav()

    x = d["market"] / d["nav"] - 1

    exp = CONTRACT["nav"]["premium_discount"]

    assert x.median() == pytest.approx(exp["median"], abs=5e-6)
    assert x.quantile(.05) == pytest.approx(exp["p05"], abs=5e-6)
    assert x.quantile(.95) == pytest.approx(exp["p95"], abs=5e-6)
    assert x.abs().max() == pytest.approx(exp["max_abs"], abs=5e-6)


def test_drift_decomposition():
    d = load_nav()

    rb = np.log(d["btc"] / d["btc"].shift(1))
    rn = np.log(d["nav"] / d["nav"].shift(1))
    rm = np.log(d["market"] / d["market"].shift(1))

    total = (rm-rb).dropna()
    nav_btc = (rn-rb).dropna()
    market_nav = (rm-rn).dropna()

    def ann(x):
        return np.exp(x.mean()*252)-1

    exp = CONTRACT["nav"]["log_return_decomposition"]

    assert ann(total) == pytest.approx(
        exp["total_market_vs_btc_drift_ann"],
        abs=1e-5
    )

    assert ann(nav_btc) == pytest.approx(
        exp["nav_vs_btc_drift_ann"],
        abs=1e-5
    )

    assert ann(market_nav) == pytest.approx(
        exp["market_vs_nav_drift_ann"],
        abs=1e-5
    )

    # Exact additive identity in log-return space.
    assert (
        total.mean()*252
    ) == pytest.approx(
        nav_btc.mean()*252 + market_nav.mean()*252,
        abs=1e-14
    )


# ------------------------------------------------------------
# GOVERNANCE
# ------------------------------------------------------------

def test_futures_scope():
    f = CONTRACT["futures"]

    assert f["empirical_backtest"] == "EXCLUDED_BY_DESIGN"
    assert f["publication_scope"] == "STRUCTURAL_ONLY"
    assert f["continuous_proxy"] == "REJECTED"
    assert f["yahoo_contract_history"] == "REJECTED"
    assert f["cme_unauthenticated_settlement_endpoint"] == "REJECTED"


def test_claim_governance():
    forbidden = CONTRACT["claim_policy"]["forbidden"]

    assert "historical CME J-5 performance claim" in forbidden
    assert "historical CME futures tracking-error claim" in forbidden
    assert "tracking difference described solely as management fees" in forbidden


# ------------------------------------------------------------
# CRYPTOGRAPHIC FREEZE
# ------------------------------------------------------------

def test_freeze_integrity():
    assert FREEZE.exists()

    freeze = json.loads(FREEZE.read_text())

    assert freeze["protocol_version"] == "1.1"

    for item in freeze["files"]:
        path = ROOT / item["path"]

        assert path.exists()
        assert sha256(path) == item["sha256"], (
            f"RESEARCH DRIFT: {item['path']}"
        )

from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

REPORT = (
    ROOT
    / "outputs/reports/PUBLICATION_ROBUSTNESS_RESULTS.json"
)

TRACKING = (
    ROOT
    / "outputs/tables/publication_robustness_tracking_v1_1.csv"
)

PREMIUM = (
    ROOT
    / "outputs/tables/publication_robustness_premium_discount_v1_1.csv"
)

CLAIMS = (
    ROOT
    / "publication/claims_registry_v1_1.json"
)


def load():
    return (
        json.loads(REPORT.read_text()),
        pd.read_csv(TRACKING),
        pd.read_csv(PREMIUM),
        json.loads(CLAIMS.read_text()),
    )


def metric(claims, key):
    return float(
        claims["metrics"][key]["value"]
    )


def test_robustness_report_contract():
    report, _, _, _ = load()

    assert report["status"] == "PASS"

    assert (
        report["primary_research_freeze_modified"]
        is False
    )

    assert (
        report["raw_provider_added"]
        is False
    )

    temporal = report["temporal_sensitivity"]

    assert (
        temporal["future_information_used"]
        is False
    )

    assert (
        temporal["exact_boundary_coverage"]
        == 1.0
    )


def test_primary_matches_frozen_claims():
    _, tracking, _, claims = load()

    row = tracking.loc[
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
        assert abs(
            float(row[column])
            - metric(claims, key)
        ) < 2e-6


def test_simple_vs_log_is_stable():
    _, tracking, _, _ = load()

    simple = tracking.loc[
        tracking["specification"]
        == "xnas_simple_primary"
    ].iloc[0]

    log = tracking.loc[
        tracking["specification"]
        == "xnas_log_sensitivity"
    ].iloc[0]

    assert simple["correlation"] > 0.9995
    assert log["correlation"] > 0.9995

    assert abs(
        simple["beta"]
        - log["beta"]
    ) < 0.001

    assert abs(
        simple["r2"]
        - log["r2"]
    ) < 0.001

    assert abs(
        simple["tracking_error_ann"]
        - log["tracking_error_ann"]
    ) < 0.0001

    assert abs(
        simple[
            "tracking_difference_ann_compounded"
        ]
        - log[
            "tracking_difference_ann_compounded"
        ]
    ) < 1e-12


def test_temporal_boundary_is_material():
    _, tracking, _, _ = load()

    synced = tracking.loc[
        tracking["specification"]
        == "xnas_simple_primary"
    ].iloc[0]

    utc = tracking.loc[
        tracking["specification"]
        == "utc00_simple_boundary_sensitivity"
    ].iloc[0]

    assert synced["correlation"] > 0.9995
    assert utc["correlation"] < 0.50

    assert (
        utc["tracking_error_ann"]
        > 0.50
    )

    assert (
        utc["tracking_error_ann"]
        > 20
        * synced["tracking_error_ann"]
    )


def test_premium_discount_tail_stability():
    _, _, premium, _ = load()

    p = premium.set_index(
        "specification"
    )

    full = p.loc["full_sample"]
    trim1 = p.loc["remove_top_1pct_abs"]
    trim5 = p.loc["remove_top_5pct_abs"]

    assert abs(
        trim1["median"]
        - full["median"]
    ) < 0.0001

    assert abs(
        trim5["median"]
        - full["median"]
    ) < 0.0001

    assert (
        full["mean_abs"]
        > trim1["mean_abs"]
        > trim5["mean_abs"]
    )

    assert (
        full["max_abs"]
        > trim1["max_abs"]
        > trim5["max_abs"]
    )


def test_robustness_sample_sizes():
    _, tracking, premium, _ = load()

    assert set(
        tracking["n"].astype(int)
    ) == {660}

    p = premium.set_index(
        "specification"
    )

    assert int(
        p.loc["full_sample", "n"]
    ) == 661

    assert int(
        p.loc["remove_top_1pct_abs", "n"]
    ) == 654

    assert int(
        p.loc["remove_top_5pct_abs", "n"]
    ) == 627


def test_robustness_claims_match_outputs():
    _, tracking, premium, claims = load()

    log = tracking.loc[
        tracking["specification"]
        == "xnas_log_sensitivity"
    ].iloc[0]

    utc = tracking.loc[
        tracking["specification"]
        == "utc00_simple_boundary_sensitivity"
    ].iloc[0]

    p = premium.set_index(
        "specification"
    )

    checks = [
        (
            metric(
                claims,
                "robust.log.correlation",
            ),
            log["correlation"],
        ),
        (
            metric(
                claims,
                "robust.log.tracking_error_ann",
            ),
            log["tracking_error_ann"],
        ),
        (
            metric(
                claims,
                "robust.utc00.correlation",
            ),
            utc["correlation"],
        ),
        (
            metric(
                claims,
                "robust.utc00.tracking_error_ann",
            ),
            utc["tracking_error_ann"],
        ),
        (
            metric(
                claims,
                "robust.pd.trim1.median",
            ),
            p.loc[
                "remove_top_1pct_abs",
                "median",
            ],
        ),
        (
            metric(
                claims,
                "robust.pd.trim5.median",
            ),
            p.loc[
                "remove_top_5pct_abs",
                "median",
            ],
        ),
    ]

    for expected, observed in checks:
        assert np.isfinite(observed)

        assert abs(
            expected
            - float(observed)
        ) < 1e-12

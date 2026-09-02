from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "publication/claims_registry_v1_1.json"
REPORT = ROOT / "outputs/reports/PUBLICATION_ROBUSTNESS_RESULTS.json"

registry = json.loads(REGISTRY.read_text())
report = json.loads(REPORT.read_text())

metrics = registry["metrics"]

premium = {
    row["specification"]: row
    for row in report["premium_discount_tail_sensitivity"]
}

log = report["log_return_sensitivity"]
utc = report["utc00_boundary_sensitivity"]
temporal = report["temporal_sensitivity"]

new_metrics = {
    "robust.log.correlation": (
        log["correlation"],
        "decimal6",
    ),
    "robust.log.beta": (
        log["beta"],
        "decimal6",
    ),
    "robust.log.r2": (
        log["r2"],
        "decimal6",
    ),
    "robust.log.tracking_error_ann": (
        log["tracking_error_ann"],
        "percent4",
    ),
    "robust.log.tracking_difference_ann": (
        log["tracking_difference_ann_compounded"],
        "percent4",
    ),

    "robust.utc00.coverage": (
        temporal["exact_boundary_coverage"],
        "percent2",
    ),
    "robust.utc00.correlation": (
        utc["correlation"],
        "decimal6",
    ),
    "robust.utc00.beta": (
        utc["beta"],
        "decimal6",
    ),
    "robust.utc00.r2": (
        utc["r2"],
        "decimal6",
    ),
    "robust.utc00.tracking_error_ann": (
        utc["tracking_error_ann"],
        "percent4",
    ),
    "robust.utc00.tracking_difference_ann": (
        utc["tracking_difference_ann_compounded"],
        "percent4",
    ),

    "robust.pd.full.mean_abs": (
        premium["full_sample"]["mean_abs"],
        "percent4",
    ),

    "robust.pd.trim1.median": (
        premium["remove_top_1pct_abs"]["median"],
        "percent4",
    ),
    "robust.pd.trim1.mean_abs": (
        premium["remove_top_1pct_abs"]["mean_abs"],
        "percent4",
    ),
    "robust.pd.trim1.p05": (
        premium["remove_top_1pct_abs"]["p05"],
        "percent4",
    ),
    "robust.pd.trim1.p95": (
        premium["remove_top_1pct_abs"]["p95"],
        "percent4",
    ),
    "robust.pd.trim1.max_abs": (
        premium["remove_top_1pct_abs"]["max_abs"],
        "percent4",
    ),

    "robust.pd.trim5.median": (
        premium["remove_top_5pct_abs"]["median"],
        "percent4",
    ),
    "robust.pd.trim5.mean_abs": (
        premium["remove_top_5pct_abs"]["mean_abs"],
        "percent4",
    ),
    "robust.pd.trim5.p05": (
        premium["remove_top_5pct_abs"]["p05"],
        "percent4",
    ),
    "robust.pd.trim5.p95": (
        premium["remove_top_5pct_abs"]["p95"],
        "percent4",
    ),
    "robust.pd.trim5.max_abs": (
        premium["remove_top_5pct_abs"]["max_abs"],
        "percent4",
    ),
}

for key, (value, fmt) in new_metrics.items():
    metrics[key] = {
        "value": float(value),
        "format": fmt,
    }

REGISTRY.write_text(
    json.dumps(
        registry,
        indent=2,
    )
    + "\n"
)

print("ROBUSTNESS CLAIMS UPDATED:", len(new_metrics))

for key in sorted(new_metrics):
    print(
        key,
        "=",
        metrics[key]["value"],
    )

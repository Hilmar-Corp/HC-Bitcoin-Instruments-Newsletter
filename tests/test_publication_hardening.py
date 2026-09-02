from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

RAW_REGISTRY = ROOT / "research/raw_sources_v1_1.json"
RAW_FREEZE = ROOT / "research/raw_freeze_v1_1.json"
CLAIMS = ROOT / "publication/claims_registry_v1_1.json"
FIGURES = ROOT / "publication/figures/manifest_v1_1.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def test_raw_freeze_exists():
    assert RAW_REGISTRY.exists()
    assert RAW_FREEZE.exists()


def test_raw_freeze_manifest_integrity():
    freeze = json.loads(RAW_FREEZE.read_text())

    assert freeze["registry_sha256"] == sha256(RAW_REGISTRY)

    for source in freeze["sources"]:
        assert len(source["sha256"]) == 64
        assert source["bytes"] > 0

        # Raw provider caches are deliberately absent from the
        # public repository. If available locally, verify them.
        path = ROOT / source["path"]

        if path.exists():
            assert sha256(path) == source["sha256"]


def test_claim_registry():
    claims = json.loads(CLAIMS.read_text())

    assert claims["version"] == "1.1"

    required = {
        "ibit.correlation",
        "ibit.beta",
        "ibit.r2",
        "ibit.tracking_error_ann",
        "ibit.tracking_difference_ann",
        "nav.premium_discount_median"
    }

    assert required.issubset(claims["metrics"].keys())


def test_futures_claims_are_forbidden():
    claims = json.loads(CLAIMS.read_text())

    blob = " ".join(
        claims["forbidden_patterns"]
    ).lower()

    assert "j-5" in blob
    assert "futures tracking error" in blob
    assert "btc=f" in blob


def test_figure_manifest_integrity_if_present():
    if not FIGURES.exists():
        return

    manifest = json.loads(FIGURES.read_text())

    for fig in manifest["figures"]:
        objects = [
            fig["figure"],
            fig["generator"],
            *fig["inputs"]
        ]

        for obj in objects:
            path = ROOT / obj["path"]

            assert path.exists()
            assert sha256(path) == obj["sha256"]

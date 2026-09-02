from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "research/raw_sources_v1_1.json"
FREEZE = ROOT / "research/raw_freeze_v1_1.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument(
    "--require-present",
    action="store_true"
)
args = parser.parse_args()

registry = json.loads(REGISTRY.read_text())
freeze = json.loads(FREEZE.read_text())

errors = []

if freeze["registry_sha256"] != sha256(REGISTRY):
    errors.append("raw source registry hash drift")

for source in freeze["sources"]:
    path = ROOT / source["path"]

    if not path.exists():
        if args.require_present:
            errors.append(
                f"missing local raw source: {source['path']}"
            )
        continue

    if sha256(path) != source["sha256"]:
        errors.append(
            f"raw source hash drift: {source['path']}"
        )

if errors:
    print("RAW INPUT VERIFICATION: FAIL")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("RAW INPUT VERIFICATION: PASS")

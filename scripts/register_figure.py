from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

MANIFEST = (
    ROOT /
    "publication/figures/manifest_v1_1.json"
)

RESEARCH_FREEZE = (
    ROOT /
    "research/freeze_v1_1.json"
)

RAW_FREEZE = (
    ROOT /
    "research/raw_freeze_v1_1.json"
)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def rel(path):
    return str(path.resolve().relative_to(ROOT.resolve()))


parser = argparse.ArgumentParser()

parser.add_argument(
    "--figure",
    required=True
)

parser.add_argument(
    "--script",
    required=True
)

parser.add_argument(
    "--inputs",
    nargs="+",
    required=True
)

parser.add_argument(
    "--id",
    required=True
)

args = parser.parse_args()

figure = Path(args.figure)
script = Path(args.script)
inputs = [Path(x) for x in args.inputs]

for p in [figure, script, *inputs]:
    if not p.exists():
        raise FileNotFoundError(p)

if not RESEARCH_FREEZE.exists():
    raise RuntimeError(
        "Research freeze missing."
    )

if not RAW_FREEZE.exists():
    raise RuntimeError(
        "Raw freeze missing."
    )

if MANIFEST.exists():
    manifest = json.loads(MANIFEST.read_text())
else:
    manifest = {
        "version": "1.1",
        "figures": []
    }

entry = {
    "id": args.id,

    "registered_at_utc":
        datetime.now(timezone.utc).isoformat(),

    "figure": {
        "path": rel(figure),
        "sha256": sha256(figure)
    },

    "generator": {
        "path": rel(script),
        "sha256": sha256(script)
    },

    "inputs": [
        {
            "path": rel(p),
            "sha256": sha256(p)
        }
        for p in inputs
    ],

    "research_freeze_sha256":
        sha256(RESEARCH_FREEZE),

    "raw_freeze_sha256":
        sha256(RAW_FREEZE)
}

manifest["figures"] = [
    x for x in manifest["figures"]
    if x["id"] != args.id
]

manifest["figures"].append(entry)

MANIFEST.write_text(
    json.dumps(
        manifest,
        indent=2
    )
)

print("FIGURE REGISTERED:", args.id)
print("Manifest:", MANIFEST)

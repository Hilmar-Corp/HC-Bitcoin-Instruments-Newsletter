from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]

REGISTRY = ROOT / "research/raw_sources_v1_1.json"
OUTPUT = ROOT / "research/raw_freeze_v1_1.json"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


registry = json.loads(REGISTRY.read_text())

records = []

for source in registry["sources"]:
    path = ROOT / source["path"]

    if not path.exists():
        raise FileNotFoundError(
            f"Missing frozen raw source: {source['path']}"
        )

    records.append({
        **source,
        "bytes": path.stat().st_size,
        "sha256": sha256(path)
    })

result = {
    "research_id": registry["research_id"],
    "version": registry["version"],
    "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "registry_sha256": sha256(REGISTRY),
    "sources": records
}

OUTPUT.write_text(json.dumps(result, indent=2))

print("=" * 72)
print("RAW DATA FREEZE V1.1")
print("=" * 72)

for r in records:
    print(
        r["sha256"][:16],
        r["id"],
        r["path"]
    )

print()
print("Output:", OUTPUT)
print("STATUS: RAW INPUTS FROZEN")
